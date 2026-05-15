@echo off
cd /d "%~dp0"
start "VoltStream Backend" cmd /k start_backend.bat
start "VoltStream Frontend" cmd /k "cd /d frontend && npm run dev -- --host 0.0.0.0"
echo VoltStream backend and frontend are starting.
echo.
echo Backend:  http://192.168.0.114:8000
echo Frontend: http://192.168.0.114:5175
echo.
echo Keep both terminal windows open while using the app.
pause
