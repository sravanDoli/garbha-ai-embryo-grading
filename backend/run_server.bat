@echo off
REM ============================================
REM Embryo Fragmentation Analysis Server
REM Location: G:\garba\deployment_new\run_server.bat
REM ============================================
color 0A
title Embryo Fragmentation API Server

echo.
echo ============================================
echo   EMBRYO FRAGMENTATION ANALYSIS SERVER
echo ============================================
echo.

REM Activate conda environment
echo [1/4] Activating environment: embryo_D...
call conda activate embryo_D
if errorlevel 1 (
    echo ERROR: Failed to activate embryo_D environment
    echo Please run: conda activate embryo_D
    pause
    exit /b 1
)
echo OK - Environment activated
echo.

REM Navigate to deployment directory
echo [2/4] Navigating to deployment directory...
cd /d G:\garba\deployment_new
if errorlevel 1 (
    echo ERROR: Failed to navigate to G:\garba\deployment_new
    pause
    exit /b 1
)
echo OK - In deployment directory
echo.

REM Check if model file exists
echo [3/4] Checking model file...
if not exist "models\best.pt" (
    echo ERROR: Model file not found!
    echo Please copy your best.pt file to: G:\garba\deployment_new\models\
    echo.
    echo Current files in models folder:
    dir /b models\*.pt 2>nul
    pause
    exit /b 1
)
echo OK - Model file found
echo.

REM Start the server
echo [4/4] Starting API server...
echo.
echo ============================================
echo   SERVER IS STARTING...
echo ============================================
echo.
echo   API Documentation: http://localhost:8000/docs
echo   Health Check:      http://localhost:8000/health
echo   Dashboard:         http://localhost:8000/dashboard
echo.
echo   Press CTRL+C to stop the server
echo ============================================
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

REM If server stops
echo.
echo ============================================
echo   SERVER STOPPED
echo ============================================
echo.
pause