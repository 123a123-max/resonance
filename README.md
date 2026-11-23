# resonance

一页共同日记 · 小组日常记录网站（React + Vite 前端，FastAPI 后端）。

## ✨ 新增功能：生活拼贴

在「共同日记」卡片点击 **🖼️ 生活拼贴**，即可使用 12 套风格模板把多张照片拼成一张海报，支持 AI 生成、本地离线排版、预览与 PNG 下载。

- 📖 使用 / 部署 / Git 分支推送完整指南：[`docs/生活拼贴-部署与Git指南.md`](docs/生活拼贴-部署与Git指南.md)
- 🎨 12 套风格完整 AI 提示词：[`docs/拼贴提示词.md`](docs/拼贴提示词.md)

## 快速运行

```bash
npm.cmd install && npm.cmd run build
backend/.venv/Scripts/python.exe -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```
打开 http://localhost:8000/

## 功能特点

- **12 套拼贴风格**：复古旅行手账、清新绿调、四季时间轴、波普撞色、INS 留白、日系盐系胶片、奶油马卡龙、清透 AI 科技磨砂、时光日历日记、街头涂鸦、文艺宣纸书香、美式复古杂志，每套均带预览示例图。
- **AI 生成 + 本地兜底**：配置 API Key 后调用 AI；未配置或失败时自动使用纯前端 Canvas 排版，离线也能出图。
- **轻量无依赖**：不引入任何重型框架，仅用 React + 原生 Canvas。
