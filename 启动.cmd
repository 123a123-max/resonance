@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-local.ps1" %*
set "exitCode=%errorlevel%"
if not "%exitCode%"=="0" pause
exit /b %exitCode%
