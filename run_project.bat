@echo off
title AIKTC Chatbot Launcher
echo ========================================================
echo        Starting AIKTC Chatbot (Backend + Frontend)
echo ========================================================

cd /d "%~dp0"

set "PYTHON_EXE=%~dp0..\python-embed\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

set "NODE_DIR=%~dp0..\node-portable\node-v20.18.0-win-x64"
if exist "%NODE_DIR%" (
    set "PATH=%NODE_DIR%;%PATH%"
)

echo Starting Backend on port 8001...
start "AIKTC Chatbot Backend (Port 8001)" cmd /k "cd /d "%~dp0backend" && "%PYTHON_EXE%" main.py"

echo Starting Frontend on port 3001...
start "AIKTC Chatbot Frontend (Port 3001)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================================
echo Chatbot servers launched!
echo - Web UI:  http://localhost:3001
echo - API Docs: http://localhost:8001/docs
echo ========================================================
pause
