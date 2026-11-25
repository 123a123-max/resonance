@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "backend\.venv\Scripts\python.exe" (
  echo [ERROR] Python environment not found: backend\.venv
  pause
  exit /b 1
)
if not exist "dist\index.html" (
  echo [ERROR] dist\index.html not found. Run: npm run build
  pause
  exit /b 1
)
echo Starting resonance ... http://localhost:8010/
start "resonance server" cmd /k "backend\.venv\Scripts\python.exe" -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8010
timeout /t 5 /nobreak >nul
start "" http://localhost:8010/

