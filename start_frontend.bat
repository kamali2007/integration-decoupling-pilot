@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo  INTEGRATION CONTROL TOWER - FRONTEND LAUNCHER
echo  React + Vite + TypeScript Enterprise Operations Dashboard
echo ===============================================================================

cd /d "%~dp0frontend"

:: Include local user node in PATH if installed there
if exist "%LOCALAPPDATA%\Programs\nodejs" (
    set "PATH=%LOCALAPPDATA%\Programs\nodejs;%PATH%"
)

:: Check Node.js availability
call node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js was not found in PATH.
    echo Please verify Node.js is installed or in %LOCALAPPDATA%\Programs\nodejs.
    pause
    exit /b 1
)

:: Install dependencies if node_modules is missing
if not exist "node_modules" (
    echo [1/2] Installing npm dependencies...
    call npm install
)

echo [2/2] Launching Vite development server on http://localhost:5173 ...
echo ===============================================================================

call npm run dev
pause
