@echo off
title VoltStream Backend
cd /d "%~dp0backend"
"%~dp0venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000
echo.
echo Backend stopped. Press any key to close this window.
pause >nul
