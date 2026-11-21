# resonance · 共同日记

React / Vite 前端与 FastAPI / SQLite 后端。

## 本次更新

- 上传时间明确按北京时间显示。接口返回带 `Z` 的 UTC 时间，并兼容旧接口没有时区的 UTC 字符串；上传分日和生成日记的日期统一按北京时间计算。
- 美化「生活拼贴」，新增「秋日手帐」「胶片旅行」「四季拼贴」。提供纸张纹理、胶带、拍立得相框、胶片边框和不同版式；装饰不依赖外部图片。
- 模板通过缩略色卡选择。手帐按每页最多六条排版，照片延迟加载；点击照片可放大。生成前可移除记录、调整顺序，生成的日记保存所选内容与顺序。
- 首页和历史日记复用同一模板组件。上传时间指上传记录的时间，不是照片 EXIF 拍摄时间。

## 本地运行

```powershell
npm ci
pip install -r backend/requirements.txt
npm run build
python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

打开 <http://localhost:8000/>；后端检查地址为 <http://localhost:8000/api/health>。
开发时可另开终端执行 `npm run dev`，前端地址为 <http://localhost:3002/>。

数据库和上传文件由 `PLOG_DATA_DIR` 指定，默认位于 `backend`。更新已有安装时请继续使用原数据目录，不要用空目录替换原数据库。

## 回归检查

```powershell
node tests/time-and-templates.cjs
python tests/test_upload_time.py
npm run build
```

后端测试使用隔离的临时数据库，不读取已有日记。检查覆盖旧版时间戳、北京时间午夜、上传/列表时间一致性，以及四套拼贴的分页、视频、空状态和文字转义。

手机、微信和 QQ 的实际显示效果仍需真机验收。自动检查不能替代真机体验检查。更多现有运行说明见 [使用版说明](./使用版说明.md)。
