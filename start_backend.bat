@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo  INTEGRATION CONTROL TOWER - BACKEND LAUNCHER
echo  FastAPI + SQLAlchemy + SQLite Canonical Gateway
echo ===============================================================================

cd /d "%~dp0backend"

:: Check Python availability
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH. Please ensure Python 3.11+ is installed.
    pause
    exit /b 1
)

:: Create virtual environment if missing
if not exist "venv" (
    echo [1/4] Creating Python virtual environment in backend/venv...
    python -m venv venv
    if errorlevel 1 (
        echo [WARNING] venv creation failed; proceeding with active system Python...
    )
)

:: Activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    echo [2/4] Activating virtual environment...
    call venv\Scripts\activate.bat
)

:: Install requirements
echo [3/4] Checking and installing Python dependencies...
python -m pip install -r requirements.txt --quiet

:: Initialize database and seed if missing
echo [4/4] Starting FastAPI backend on http://127.0.0.1:8000 ...
echo [INFO] Interactive Swagger Documentation: http://127.0.0.1:8000/docs
echo ===============================================================================

python run.py
pause
