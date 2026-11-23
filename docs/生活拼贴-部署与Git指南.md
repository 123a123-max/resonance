# 生活拼贴功能 · 部署与 Git 分支完全指南

本文档覆盖三部分：① 功能说明与使用方法；② AI 生成的可选配置；③ 从创建分支到推送、合并、部署的完整 Git 命令。
所有命令均可直接复制执行（在 Windows 的 Git Bash / PowerShell 中均可，路径按你的实际位置调整）。

---

## 一、功能说明

### 入口
打开网站 → 找到「共同日记」卡片 → 点击右上角 **🖼️ 生活拼贴** 按钮，弹出工作台。

### 使用流程
1. **选风格**：12 套模板（复古旅行手账 / 清新绿调 / 四季时间轴 / 波普撞色 / INS 留白 / 日系盐系胶片 / 奶油马卡龙 / 清透 AI 科技磨砂 / 时光日历日记 / 街头涂鸦 / 文艺宣纸书香 / 美式复古杂志），每套都有 CSS 绘制的预览示例图，可点顶部标签按分类筛选。
2. **传照片**：点「点击选择多张照片」可一次多选（最多 12 张），也可点「用今天的日记照片」快捷导入当天记录。可逐张移除。
3. **填标题**（可选）并点「复制 AI 提示词」可取到该风格的提示词。
4. **生成**：
   - 「✨ AI 生成拼贴」：优先调用后端 AI 接口；**未配置 AI 时会自动降级为本地排版**，不会报错卡住。
   - 「本地排版」：强制用纯前端 Canvas 生成，完全离线可用。
5. **预览与下载**：生成后可放大预览，点「⬇️ 下载 PNG」保存到本地。

### 兼容性
- 只依赖项目已有的 React + 原生 Canvas，未引入任何重型框架。
- 新增文件：`src/collage/`（4 个）、`backend/collage_api.py`、`docs/`（2 个）。
- 修改文件：`src/App.tsx`（4 处增量）、`src/styles.css` 无改动（样式在 collage.css 内）、`backend/main.py`（挂载 1 处）。

---

## 二、AI 生成配置（可选，不配也能用本地排版）

后端接口 `/api/collage/generate` 兼容 OpenAI `/v1/images/edits` 格式。配置方式：在启动后端前设置环境变量。

### Windows PowerShell（临时，仅当前窗口有效）
```powershell
$env:COLLAGE_AI_API_KEY  = "你的密钥"
$env:COLLAGE_AI_BASE_URL = "https://api.openai.com/v1"   # 或其他兼容服务
$env:COLLAGE_AI_MODEL    = "gpt-image-1"
# 再启动后端
.\backend\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

### Git Bash（临时）
```bash
export COLLAGE_AI_API_KEY="你的密钥"
export COLLAGE_AI_BASE_URL="https://api.openai.com/v1"
export COLLAGE_AI_MODEL="gpt-image-1"
backend/.venv/Scripts/python.exe -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

### 变量说明
| 变量 | 必填 | 默认 | 说明 |
|---|---|---|---|
| `COLLAGE_AI_API_KEY` | 否 | 空 | 不填则接口返回 503，前端自动用本地排版 |
| `COLLAGE_AI_BASE_URL` | 否 | `https://api.openai.com/v1` | 任何兼容 OpenAI 图像接口的服务地址 |
| `COLLAGE_AI_MODEL` | 否 | `gpt-image-1` | 图像模型名 |
| `COLLAGE_AI_TIMEOUT` | 否 | `120` | 超时秒数 |

> 安全提示：切勿把密钥写进代码或提交到 GitHub。只用环境变量注入。

---

## 三、本地构建与运行

```bash
# 进入项目目录
cd C:/Users/lenovo/WorkBuddy/2026-11-22-11-02-32/resonance

# 前端：安装依赖 + 构建（改动已构建好，改代码后需重跑 build）
npm.cmd install
npm.cmd run build

# 后端：虚拟环境已就绪，启动服务（一个端口同时提供网页 + 接口）
backend/.venv/Scripts/python.exe -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

打开 http://localhost:8000/ 。局域网手机访问：http://192.168.236.127:8000/ （IP 会变，以实际为准）。

> 注意：本项目依赖「纯 Python 版 SQLAlchemy」。若重建虚拟环境后报 `DLL load failed ... _cache_key_cy`，
> 执行：`backend/.venv/Scripts/python.exe -m pip install --force-reinstall --no-deps https://files.pythonhosted.org/packages/7a/ee/9926603a1f7e88b41bc0d1e068e889fc84981553fb4e6037426d6b174da3/sqlalchemy-2.1.9-py3-none-any.whl`

---

## 四、Git 分支创建 → 提交 → 推送到 GitHub

当前目录是 ZIP 解压得到的，**没有 .git**。若你还没初始化仓库，按「场景 A」；若本地已有 git 仓库，跳到「场景 B」。

### 场景 A：首次初始化本地仓库并关联 GitHub

```bash
cd C:/Users/lenovo/WorkBuddy/2026-11-22-11-02-32/resonance

# 1. 初始化
git init

# 2. 关联远程仓库（换成你自己的仓库地址）
git remote add origin https://github.com/123a123-max/resonance.git

# 3. 确认分支名为 main
git branch -M main
```

### 场景 B：已有仓库，直接新建功能分支

```bash
cd C:/Users/lenovo/WorkBuddy/2026-11-22-11-02-32/resonance

# 先拉取最新代码，避免冲突
git checkout main
git pull origin main

# 新建并切换到功能分支
git checkout -b feature/life-collage
```

> 若你是场景 A，也要建功能分支：`git checkout -b feature/life-collage`

### 提交改动（通用）

```bash
# 查看改动，确认只包含本次功能相关文件
git status

# 暂存全部改动
git add .

# 提交（写清楚提交信息）
git commit -m "feat: 新增生活拼贴功能（12套风格模板 + AI生成 + 本地兜底 + 提示词文档）"
```

### 推送分支到 GitHub（通用）

```bash
# 首次推送该分支（-u 建立上游关联）
git push -u origin feature/life-collage
```

推送时会要求 GitHub 身份认证。**推荐用 Personal Access Token (PAT) 代替密码**：

1. 打开 GitHub → 右上角头像 → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token，勾选 `repo` 权限，生成后复制（只显示一次）。
3. 推送时用户名填 GitHub 用户名，密码处粘贴 Token。

如果 push 因网络失败（本机访问 github.com 可能被限制），可改用下面任一方式：
- 配置代理：`git config --global http.proxy http://127.0.0.1:7890`（端口按你的代理实际值）
- 或手动在 GitHub 网页建仓库后，用 GitHub Desktop 客户端推送
- 或把 GitHub 仓库地址换成可用的镜像/加速地址

---

## 五、从分支合并到主干（main）

### 方式一：网页端 Pull Request（推荐）

1. 推送后，打开 GitHub 仓库页面，会出现 "Compare & pull request" 提示，点击。
2. 确认 `feature/life-collage` → `main`，填写说明，点 "Create pull request"。
3. 检查无误后点 "Merge pull request"，再 "Confirm merge"。
4. 本地同步：
```bash
git checkout main
git pull origin main
```

### 方式二：命令行直接合并

```bash
git checkout main
git pull origin main
git merge feature/life-collage
git push origin main

# 合并后可删除功能分支（可选）
git branch -d feature/life-collage
git push origin --delete feature/life-collage
```

---

## 六、部署上线

### 本机长期运行（Windows 计划任务 / NSSM）
把启动命令做成 `.bat`：
```bat
@echo off
cd /d C:\Users\lenovo\WorkBuddy\2026-11-22-11-02-32\resonance
backend\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```
双击即可启动；配合「任务计划程序」可设开机自启。

### 云端部署（项目已带 render.yaml）
本项目根目录有 `render.yaml`，可直接导入 Render.com 等支持该文件的平台。部署前记得：
- 构建命令：`npm install && npm run build`
- 启动命令：`python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port $PORT`
- 在平台环境变量里配置 `COLLAGE_AI_API_KEY` 等（可选）

### 公网临时访问（Cloudflare 隧道）
```bash
cloudflared tunnel --protocol http2 --url http://127.0.0.1:8000
```
把生成的 HTTPS 地址发给朋友即可（临时域名每次启动会变；当前鉴权不完善，仅限受控范围试用）。

---

## 七、常见问题

**Q：提示词在哪里看？**
A：`docs/拼贴提示词.md`，或在弹窗里点「复制提示词」按钮。

**Q：AI 生成报「AI 服务不可用」怎么办？**
A：说明未配置 Key 或网络不通，前端会自动用本地排版生成，功能不受影响。要启用 AI 请按第二节配置环境变量。

**Q：本地排版效果够用吗？**
A：本地 Canvas 已为 12 套风格分别实现了差异化布局（留白 / 时间轴 / 波普 / 日历网格 / 错落手账等）+ 纹理 + 装饰，无需联网即可出图并下载，适合日常记录；AI 生成在人像保真和复杂质感上更强。

**Q：会不会影响原有共同日记功能？**
A：不会。所有改动都是增量：新增独立文件 + App.tsx 增加 4 处入口/挂载代码 + main.py 挂载 1 行路由，未改动任何原有逻辑。
