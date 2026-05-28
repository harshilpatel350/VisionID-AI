@echo off
setlocal EnableDelayedExpansion
title VisionID AI - Server Launcher
cls

:: Define Colors for Windows 10+ ANSI
set "ESC="
set "RED=%ESC%[91m"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "BLUE=%ESC%[94m"
set "CYAN=%ESC%[96m"
set "RESET=%ESC%[0m"

echo %CYAN%===================================================%RESET%
echo %BLUE%               VisionID AI Launcher%RESET%
echo %CYAN%===================================================%RESET%
echo.

:: 1. Check & Setup Backend (Python)
echo %YELLOW%[1/3] Checking Backend Environment...%RESET%
if not exist "backend\venv" (
    echo %RED%[INFO] Virtual environment missing. Creating one now...%RESET%
    cd backend
    python -m venv venv
    if errorlevel 1 (
        echo %RED%[ERROR] Failed to create virtual environment. Ensure Python is installed and in PATH.%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%[INFO] Virtual environment created.%RESET%
    echo %YELLOW%[INFO] Installing requirements...%RESET%
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    deactivate
    cd ..
) else (
    echo %GREEN%[OK] Backend venv found.%RESET%
)

:: 2. Check & Setup Frontend (Node)
echo.
echo %YELLOW%[2/3] Checking Frontend Environment...%RESET%
if not exist "frontend\node_modules" (
    echo %RED%[INFO] node_modules missing. Installing dependencies...%RESET%
    cd frontend
    call npm install
    cd ..
) else (
    echo %GREEN%[OK] Frontend node_modules found.%RESET%
)

:: 2.5 Run DB Migrations
echo.
echo %YELLOW%[2.5/3] Applying Database Migrations...%RESET%
if exist "backend\venv\Scripts\alembic.exe" (
    set "PYTHONPATH=%~dp0backend"
    call backend\venv\Scripts\alembic.exe -c backend\alembic.ini upgrade head
    if errorlevel 1 (
        echo %RED%[WARN] Alembic migration failed. You can re-run: backend\venv\Scripts\alembic.exe -c backend\alembic.ini upgrade head%RESET%
    ) else (
        echo %GREEN%[OK] Database schema is up to date.%RESET%
    )
) else (
    echo %RED%[WARN] Alembic not found in venv. Skipping migrations.%RESET%
)

:: 3. Start Services
echo.
echo %YELLOW%[3/3] Starting Services...%RESET%

echo %GREEN%[START] Booting Backend Server (localhost:8001)...%RESET%
start "VisionID AI Backend" /D "%~dp0" cmd /k "title VisionID AI - Backend && set PYTHONPATH=%~dp0backend && backend\venv\Scripts\python.exe -m app.main"

:: Wait 3 seconds for backend to start up
timeout /t 3 /nobreak >nul

echo %GREEN%[START] Booting Frontend Next.js App (localhost:3000)...%RESET%
start "VisionID AI Frontend" /D "%~dp0frontend" cmd /k "title VisionID AI - Frontend && npm run dev"

echo.
echo %CYAN%===================================================%RESET%
echo %GREEN%  VisionID AI is now starting up!%RESET%
echo.
echo   - Backend API:  %BLUE%http://localhost:8001%RESET%
echo   - API Docs:     %BLUE%http://localhost:8001/docs%RESET%
echo   - Frontend:     %BLUE%http://localhost:3000%RESET%
echo %CYAN%===================================================%RESET%
echo.
echo %YELLOW%[INFO] Launching browser in 3 seconds...%RESET%
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo Press any key to exit this launcher window...
echo (The backend and frontend console windows will remain open)
pause >nul

