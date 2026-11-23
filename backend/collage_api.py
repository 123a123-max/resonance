"""
生活拼贴 - AI 生成接口（可选模块）
==================================================================
设计目标：
  * 低侵入：独立 APIRouter，主程序只需 include_router 一行即可挂载。
  * 零新增依赖：仅用 Python 标准库 (urllib) 调用 OpenAI 兼容的图像接口，
    不强制安装 httpx / openai SDK，兼容原有依赖清单。
  * 优雅降级：未配置 API Key 时返回 503，前端会自动切换到本地 Canvas 排版。

支持的服务（通过环境变量切换，凡是兼容 OpenAI /v1/images/edits 的均可）：
  COLLAGE_AI_BASE_URL   例如 https://api.openai.com/v1  （默认）
  COLLAGE_AI_API_KEY    你的密钥（必填，未设置则本接口不可用）
  COLLAGE_AI_MODEL      例如 gpt-image-1（默认）
  COLLAGE_AI_TIMEOUT    超时秒数（默认 120）

请求：multipart/form-data
  images          一个或多个图片文件
  prompt          正面提示词
  negative_prompt 负面提示词（部分模型不支持时自动忽略）
  style_id        模板 id（仅用于命名，不影响生成）
  title           标题（可选）

响应：{ "ok": true, "image": "data:image/png;base64,..." }
"""

import os
import json
import base64
import secrets
import urllib.request
import urllib.error
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

router = APIRouter(prefix="/api/collage", tags=["collage"])

# 上传目录：与主程序共用 backend/uploads，保证 /uploads 静态路由可直接访问
UPLOADS = Path(os.environ.get("PLOG_DATA_DIR", str(Path(__file__).resolve().parent))) / "uploads"


@router.post("/generate")
async def generate_collage(
    images: list[UploadFile] = File(...),
    prompt: str = Form(...),
    negative_prompt: str = Form(""),
    style_id: str = Form("collage"),
    title: str = Form(""),
):
    """调用 AI 图像模型，把多张照片融合成指定风格的拼贴图。"""
    api_key = os.environ.get("COLLAGE_AI_API_KEY", "").strip()
    if not api_key:
        # 前端收到 503 会自动降级为本地 Canvas 排版
        raise HTTPException(
            status_code=503,
            detail="未配置 COLLAGE_AI_API_KEY，已使用本地排版",
        )

    if not images:
        raise HTTPException(status_code=400, detail="请至少上传一张图片")

    base_url = os.environ.get("COLLAGE_AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("COLLAGE_AI_MODEL", "gpt-image-1")
    timeout = int(os.environ.get("COLLAGE_AI_TIMEOUT", "120"))

    # ---- 组装 OpenAI 兼容的 multipart /images/edits 请求 ----
    boundary = "----resonanceCollage" + secrets.token_hex(12)
    body = bytearray()

    def add_field(name: str, value: str):
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")

    def add_file(name: str, filename: str, content: bytes, mime: str):
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
        body.extend(content)
        body.extend(b"\r\n")

    add_field("model", model)
    add_field("prompt", prompt)
    add_field("size", "1024x1024")
    add_field("n", "1")
    # 部分模型（如 gpt-image-1）不支持 response_format，默认返回 b64_json
    if negative_prompt:
        # 以自然语言方式附加负面约束，兼容不支持独立字段的模型
        add_field("prompt", prompt + " | Avoid: " + negative_prompt)

    for idx, image in enumerate(images[:12]):
        content = await image.read()
        mime = image.content_type or "image/png"
        add_file("image[]", f"photo-{idx + 1}.png", content, mime)

    body.extend(f"--{boundary}--\r\n".encode())

    url = f"{base_url}/images/edits"
    req = urllib.request.Request(url, data=bytes(body), method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:300]
        raise HTTPException(status_code=502, detail=f"AI 服务返回错误 {exc.code}: {detail}")
    except Exception as exc:  # noqa: BLE001 - 网络异常统一转成 502
        raise HTTPException(status_code=502, detail=f"AI 服务调用失败: {exc}")

    # ---- 解析返回结果：优先 b64_json，其次 url ----
    data = (result.get("data") or [{}])[0]
    b64 = data.get("b64_json")
    image_data_url = ""
    if b64:
        image_data_url = f"data:image/png;base64,{b64}"
    elif data.get("url"):
        image_url = data["url"]
        try:
            with urllib.request.urlopen(image_url, timeout=30) as resp:
                raw = resp.read()
            image_data_url = "data:image/png;base64," + base64.b64encode(raw).decode()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"下载 AI 结果图失败: {exc}")
    else:
        raise HTTPException(status_code=502, detail="AI 服务未返回图片数据")

    # 同时落盘一份到 uploads，便于长期保存 / 分享
    image_url = ""
    try:
        UPLOADS.mkdir(parents=True, exist_ok=True)
        filename = f"collage-{style_id}-{secrets.token_hex(8)}.png"
        (UPLOADS / filename).write_bytes(base64.b64decode(b64)) if b64 else None
        image_url = f"/uploads/{filename}"
    except Exception:
        image_url = ""  # 落盘失败不影响返回

    return {"ok": True, "image": image_data_url, "image_url": image_url}
