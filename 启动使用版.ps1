$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$oldBackend = 'C:\Users\LENOVO\Documents\Codex\2026-10-28\bereal-plog-moments-plog-iphone-android\backend'
$pythonPath = Join-Path $oldBackend '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw '未找到原来的 Python 环境，请先安装 backend/requirements.txt 中的依赖。'
}
# Keep the existing database and media instead of silently starting an empty group store.
$env:PLOG_DATA_DIR = $oldBackend
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'dist\index.html'))) {
    throw '未找到构建文件，请先运行 npm.cmd run build。'
}
Write-Host 'resonance 使用版：http://localhost:8000/。请先停止旧后端，保持此窗口运行。'
& $pythonPath -m uvicorn main:app --app-dir (Join-Path $PSScriptRoot 'backend') --host 0.0.0.0 --port 8000
