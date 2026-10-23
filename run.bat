@echo off
REM ==============================================================================
REM Amazon Order Analysis - Windows Point-and-Click Launcher
REM Double-click this file in Windows File Explorer to launch the dashboard!
REM ==============================================================================
cd /d "%~dp0"

echo.
echo ====================================================================
echo   📦 Launching Amazon Order Analysis Dashboard...
echo ====================================================================
echo.

IF EXIST ".venv\Scripts\python.exe" (
    SET "PY_BIN=.venv\Scripts\python.exe"
) ELSE IF EXIST "venv\Scripts\python.exe" (
    SET "PY_BIN=venv\Scripts\python.exe"
) ELSE (
    SET "PY_BIN=python"
)

echo Running analytics pipeline...
"%PY_BIN%" main.py

echo.
echo 🌐 Starting local web server...
echo Your browser will open automatically at http://localhost:8000/dashboard.html
echo Keep this window open while using the dashboard. Press Ctrl+C to close.
echo.

"%PY_BIN%" main.py --serve
pause

