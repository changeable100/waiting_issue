@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" web_server.py --open
) else (
  python web_server.py --open
)
if errorlevel 1 (
  echo.
  echo Demo startup failed. Check Python and port 8765, then see README.md.
  pause
)
