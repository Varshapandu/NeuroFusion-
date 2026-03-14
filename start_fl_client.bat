@echo off
REM Federated Learning Client Launcher for Windows

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo Starting Federated Learning Client
echo ============================================================
echo.

REM Get project root
cd /d "%~dp0"

REM Parse command line arguments
set "SERVER_ADDRESS=127.0.0.1:8082"
set "CLIENT_ID=1"

if not "%~1"=="" set "SERVER_ADDRESS=%~1"
if not "%~2"=="" set "CLIENT_ID=%~2"

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo Server Address: !SERVER_ADDRESS!
echo Client ID: !CLIENT_ID!
echo.

REM Start client
python federated/start_client.py --server-address !SERVER_ADDRESS! --client-id !CLIENT_ID!

pause
