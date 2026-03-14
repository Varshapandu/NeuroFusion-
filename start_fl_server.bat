@echo off
REM Federated Learning Server Launcher for Windows

echo.
echo ============================================================
echo Starting Federated Learning Server
echo ============================================================
echo.

REM Get project root
cd /d "%~dp0.."

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Get IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    set "IP=%%a"
    goto :got_ip
)

:got_ip
set IP=%IP: =%

echo Server IP Address: %IP%
echo Server Port: 8082
echo.

REM Start server
python federated/start_server.py --server-address %IP%:8082 --num-rounds 3

pause
