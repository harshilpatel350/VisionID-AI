@echo off
title VisionID AI - Launcher
cls

echo ===================================================
echo               VisionID AI Launcher
echo ===================================================
echo.

:: Check for Backend Virtual Environment
if not exist "backend\venv" (
    echo [WARNING] Backend virtual environment 'venv' was not found at 'backend\venv'.
    echo Please make sure you have created the virtual environment and installed requirements.
    echo.
    pause
    exit /b 1
)

:: Check for Frontend node_modules and install if missing
if not exist "frontend\node_modules" (
    echo [INFO] frontend/node_modules not found. Running 'npm install' inside frontend directory...
    cd frontend
    call npm install
    cd ..
    echo.
)

echo [INFO] Starting VisionID AI Backend...
start "VisionID AI Backend" /D "%~dp0backend" cmd /k "venv\Scripts\python.exe -m app.main"

echo [INFO] Starting VisionID AI Frontend...
start "VisionID AI Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

echo.
echo ===================================================
echo   VisionID AI is starting up!
echo.
echo   - Backend:  http://localhost:8001
echo   - API Docs: http://localhost:8001/docs
echo   - Frontend: http://localhost:3000
echo.
echo   Separate console windows have been opened for 
echo   backend and frontend processes.
echo ===================================================
echo.
pause
