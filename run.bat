@echo off
setlocal EnableExtensions
REM ==============================================================================
REM Amazon Order Analysis - Windows One-Click Launcher
REM NOTE: no parentheses inside echo text within IF blocks - they break cmd.exe.
REM ==============================================================================
cd /d "%~dp0"
chcp 65001 >nul 2>nul

echo.
echo ====================================================================
echo  Amazon Order Analysis ^& Intelligence Dashboard
echo ====================================================================
echo.

REM ---- 1. Find a REAL Python 3.10+ (skips the Microsoft Store stub) ----
echo [1/5] Checking Python...
set "PY_SYS="
py -3 -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3,10) else 1)" >nul 2>nul
if %ERRORLEVEL% EQU 0 set "PY_SYS=py -3"
if defined PY_SYS goto :py_ok
python -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3,10) else 1)" >nul 2>nul
if %ERRORLEVEL% EQU 0 set "PY_SYS=python"
if defined PY_SYS goto :py_ok

echo.
echo ERROR: Python 3.10 or newer was not found.
echo Install it from https://www.python.org/downloads/ and tick "Add Python to PATH".
echo If Windows opens the Microsoft Store instead, disable the python.exe alias in
echo Settings - Apps - Advanced app settings - App execution aliases.
echo.
pause
exit /b 1

:py_ok
echo   OK: using %PY_SYS%

REM ---- 2. uv (fast package manager) + virtual environment + dependencies ----
echo [2/5] Setting up environment with uv...
set "UV_CMD="
call :find_uv
if defined UV_CMD goto :uv_ok

echo   uv not found - installing it, one time...
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>nul
set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
call :find_uv
if defined UV_CMD goto :uv_ok

REM Last resort: pip is used ONLY to bootstrap uv itself
%PY_SYS% -m pip install --user --upgrade uv
call :find_uv
if defined UV_CMD goto :uv_ok

echo ERROR: could not install uv. See https://docs.astral.sh/uv/getting-started/installation/
goto :fail

:uv_ok
echo   OK: using %UV_CMD%
set "PY_BIN=.venv\Scripts\python.exe"
if exist ".venv" if not exist "%PY_BIN%" rmdir /s /q ".venv"
if not exist "%PY_BIN%" %UV_CMD% venv .venv
if errorlevel 1 goto :fail
%UV_CMD% pip install --python "%PY_BIN%" "duckdb>=1.0.0" "pandas>=2.0.0" "python-dateutil"
if errorlevel 1 goto :fail
echo   OK: dependencies installed
goto :after_uv

:find_uv
where uv >nul 2>nul
if not errorlevel 1 (
    set "UV_CMD=uv"
    exit /b 0
)
%PY_SYS% -m uv --version >nul 2>nul
if not errorlevel 1 set "UV_CMD=%PY_SYS% -m uv"
exit /b 0

:after_uv

REM ---- 3. Chart.js (needed for the graphs) - downloaded directly if not present ----
echo [3/5] Checking Chart.js...
"%PY_BIN%" -m src.chartjs
if errorlevel 1 echo   WARN: could not download Chart.js - graphs will not render

REM ---- 4 + 5. Build dashboard and serve ----
echo [4/5] Processing Amazon orders...
echo [5/5] Starting dashboard at http://localhost:8000/dashboard.html
echo Keep this window open while using the dashboard. Press Ctrl+C to stop.
echo.
"%PY_BIN%" main.py --serve %*
if errorlevel 1 goto :fail
goto :end

:fail
echo.
echo ERROR: Something went wrong - see the messages above.
pause
exit /b 1

:end
pause