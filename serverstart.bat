@echo off
REM =============================================================
REM  serverstart.bat
REM  Starts the FastAPI backend (with venv) + React/Vite frontend
REM  each in its own terminal window.
REM  Double-click this file to launch the full project.
REM =============================================================

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"
set "VENV_PYTHON=%BACKEND_DIR%\venv\Scripts\python.exe"
set "VENV_ACTIVATE=%BACKEND_DIR%\venv\Scripts\activate.bat"

REM --- Preflight: check venv exists ----------------------------
if not exist "%VENV_PYTHON%" (
    echo.
    echo [ERROR] Python virtual environment not found.
    echo         Expected: %BACKEND_DIR%\venv
    echo.
    echo Run these commands once to set it up:
    echo   cd /d %BACKEND_DIR%
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM --- Preflight: warn if .env missing -------------------------
if not exist "%BACKEND_DIR%\.env" (
    echo.
    echo [WARNING] backend\.env not found.
    echo          Email and recording will use defaults.
    echo          Copy .env.example to .env and fill in your values.
    echo.
    timeout /t 3 /nobreak >nul
)

REM --- Start Backend -------------------------------------------
echo.
echo [1/2] Starting Backend (FastAPI + uvicorn)...
start "HireMind Backend" cmd /k "cd /d "%BACKEND_DIR%" && call "%VENV_ACTIVATE%" && python run.py"

REM --- Wait for backend to boot --------------------------------
echo [   ] Waiting 4 seconds for backend to boot...
timeout /t 4 /nobreak >nul

REM --- Start Frontend ------------------------------------------
echo [2/2] Starting Frontend (React + Vite)...
start "HireMind Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

REM --- Done ----------------------------------------------------
echo.
echo =============================================================
echo   HireMind is running in 2 separate windows:
echo.
echo   Backend  API  :  http://127.0.0.1:8000
echo   API Docs      :  http://127.0.0.1:8000/docs
echo   Frontend App  :  http://localhost:5173
echo =============================================================
echo.
echo Press any key to close this launcher window.
echo The Backend and Frontend windows will keep running.
echo.
pause >nul