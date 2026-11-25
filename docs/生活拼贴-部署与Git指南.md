# 生活拼贴 · 部署与 Git 分支操作指南

本文档对应本次交付的分支 **`feature/life-collage-dynamic-layout`**：在原有 resonance 网站上新增「生活拼贴」内联设置条，14 种风格模板，照片直接取今日已上传内容，并且**按照片数量动态排版、同一风格每次生成都换一种排布**。

---

## 一、功能说明（与约定逐条对应）

入口固定为：**「共同日记」卡片 → tabs 第一个标签「生活拼贴」**。点击后标签下方**内联展开设置条**，不弹窗、不在右上角加按钮、不重复上传。

| 你的要求 | 实现方式 |
|---|---|
| 点击生活拼贴后展示设置 | tab 切换 `setTemplate('a')`，条件渲染 `TemplateCollagePanel`，挂在 tabs 下方 |
| 在里面可以选择风格 | 14 个风格按钮网格，点选后状态 `styleId` 立即变化 |
| 点击风格后右侧小框展示模板 | `.collage-preview-box` 内 `<img src={style.image}>`，随风格实时切换 |
| 立即生成带上传照片的该风格拼贴图 | 原生 Canvas：模板底图 + 今日照片按空位贴入 + 导出 JPG |
| 照片来源直接用今日照片 | 从 `store.moments` 过滤 `kind==='image'`，`assetId` 走 IndexedDB blob URL，服务端照片走 `media` URL |
| 一定根据照片数量排版 | `buildLayout()`：1–4 张选空位子集 + 空位转便签卡；5–8 张拆双图格；>8 取前 8 张并提示 |
| 主打自由随性 | 对角线/随机空位组合、照片轻度打乱、便签与手绘点缀随机 |
| 同风格多次点击生成不同模板 | 每次换随机种子，改变空位组合/照片分配/便签文案/点缀；**可以完成**（见下方说明） |
| 兼容原网站、不引入重型框架 | 只加 3 个 TS/TSX 文件 + CSS，依赖仅有项目原有的 React |

> **关于“不同次点击同一风格生成不同模板”的可行性结论：可以完成。** 实现方式是保持风格美术底图一致（否则就不是“同一风格”了），用随机种子驱动**成品的排布与点缀**发生变化：空位组合、照片先后、便签文案、边角手绘。点结果面板里的「再来一张」即可立刻换一版。若你要求的是“连模板底图美术都完全不同”，那需要为每个风格离线预生成多套底图（14 风格 × N 套），也能做，但会显著增加仓库体积，当前版本未采用。

### 技术清单

- 前端：React + TypeScript + Vite；合成只用浏览器原生 Canvas 2D，无第三方图像库。
- 模板：`public/assets/collage/template-*.jpg` 共 14 张，900×1600（9:16），由 `tools/make_*.py` 用 PIL 生成；照片空位坐标写在 `src/collage/templateStyles.ts`，与脚本严格对齐。
- 素材：Pexels License / Wikimedia Commons，来源见 `public/assets/collage/*/SOURCES.json`。

---

## 二、本地运行与部署

### 2.1 前端

```bash
cd resonance
npm install
npx tsc --noEmit          # 只做类型检查
npm run build             # 类型检查 + Vite 打包到 dist/
npm run dev               # 开发：0.0.0.0:3002，手机可同局域网访问
npm run preview           # 预览 dist/
```

### 2.2 后端（拼贴不依赖，其他功能需要）

```bash
# Windows
backend/.venv/Scripts/python.exe -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
# macOS / Linux
source backend/.venv/bin/activate && uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

前端 API 地址由 `src/App.tsx` 的 `API` 常量决定：本地开发指向 `http://<主机>:8000/api`，线上同源走 `/api`；可用 `.env` 的 `VITE_API_BASE_URL` 覆盖。后端已配置 `allow_origins=['*']`，因此服务端照片 URL 可被 Canvas 安全读取。

### 2.3 部署

把 `dist/` 部署到任意静态托管（Nginx / Vercel / Netlify / 腾讯云静态网站均可）；若用同一域名反代 `/api` 到后端，前端 API 会自动走同源。无需为拼贴功能增加任何服务端接口或密钥。

---

## 三、新建分支、提交、推送（完整步骤）

本次交付**新建**分支 `feature/life-collage-dynamic-layout`，不覆盖已有的 `feature/life-collage-integration`。

```bash
cd resonance

# 1. 确认当前改动（应看到 App.tsx、src/collage/*、public/assets/collage/*、tools/*、docs/*）
git status

# 2. 从当前分支新建并切换
git checkout -b feature/life-collage-dynamic-layout

# 3. 全部加入暂存（含 14 张模板、素材、生成脚本、文档）
git add -A

# 4. 提交
git commit -m "feat: 生活拼贴动态排版与随机变体（14 风格 + 今日照片 + 内联设置条）"

# 5. 推送并建立上游跟踪
git push -u origin feature/life-collage-dynamic-layout
```

### 3.1 如果你想从主干新建（常规做法）

```bash
git fetch origin
git checkout -b feature/life-collage-dynamic-layout origin/main
# 把本次改动的文件复制进工作区后：
git add -A
git commit -m "feat: 生活拼贴动态排版与随机变体"
git push -u origin feature/life-collage-dynamic-layout
```

### 3.2 推送失败的处理

本项目环境曾出现 SSL / schannel 报错。推荐用 GitHub CLI 接管认证：

```bash
gh auth login
gh repo set-default 123a123-max/resonance
git push -u origin feature/life-collage-dynamic-layout
```

若 GitHub 仓库尚未创建远程分支，也可先去网页端 `Branches → New branch` 建好同名分支再推送。

---

## 四、合并到主分支

### 4.1 网页端（推荐）

1. 打开 `https://github.com/123a123-max/resonance`
2. **Pull requests → New pull request**
3. base 选 `main`（或 `master`），compare 选 `feature/life-collage-dynamic-layout`
4. 填写标题与说明，提交 PR；确认无冲突后点 **Merge pull request**

### 4.2 命令行

```bash
git checkout main
git pull origin main
git merge --no-ff feature/life-collage-dynamic-layout
git push origin main
```

---

## 五、本次改动文件清单

| 文件 | 说明 |
|---|---|
| `src/App.tsx` | tab 纯切换；「生活拼贴」下插入内联设置条组件；无弹窗、无重复上传 |
| `src/collage/TemplateCollagePanel.tsx` | 内联设置条：风格选择、今日照片信息、模板预览、生成/再来一张/下载 |
| `src/collage/templateStyles.ts` | 14 种风格配置与照片空位坐标（4-seasons 为纵向四段时间轴） |
| `src/collage/templateRenderer.ts` | Canvas 合成 + 动态排版（`buildLayout`）+ 随机变体（种子）+ 便签卡与手绘点缀 |
| `src/collage/collage.css` | 内联设置条与结果面板样式（响应式） |
| `public/assets/collage/template-*.jpg` | 14 张 9:16 模板成图（本次全部专项训练完成） |
| `public/assets/collage/pexels/` | 277 张免费授权素材与 `SOURCES.json` |
| `tools/make_*_template.py` | 14 个专项模板生成脚本（PIL，可重跑调参） |
| `docs/拼贴提示词.md` | 14 风格提示词 + 动态排版/随机变体通用提示词 |
| `docs/生活拼贴-部署与Git指南.md` | 本文档 |

---

## 六、验证清单

- [x] `npx tsc --noEmit` 通过
- [x] `npm run build` 通过
- [x] 用 PIL 模拟 1/2/3/4/5/6/8 张照片：所有空位均被照片或便签填满，双图格拆分正确
- [ ] 打开网站 → 共同日记 → 点「生活拼贴」tab → 内联设置条展开（无弹窗）
- [ ] 切换风格 → 右侧小框预览随之变化
- [ ] 今日有照片时，「立即生成」产出拼贴图、可下载、点「再来一张」排布变化
- [ ] 今日无照片时给出友好提示
- [ ] 手机浏览器同样可用
