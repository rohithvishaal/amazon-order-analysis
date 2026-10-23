@echo off
REM ==============================================================================
REM Amazon Order Analysis & Intelligence Dashboard - Windows One-Click Launcher
REM Double-click this file in Windows File Explorer to launch the dashboard!
REM ==============================================================================
cd /d "%~dp0"

echo.
echo ====================================================================
echo   📦 Amazon Order Analysis ^& Intelligence Dashboard
echo ====================================================================
echo.

REM 1. Check for Python
echo [1/4] Checking Python installation...

SET "PY_SYS="

where python >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    SET "PY_SYS=python"
) ELSE (
    where py >nul 2>nul
    IF %ERRORLEVEL% EQU 0 (
        SET "PY_SYS=py -3"
    )
)

IF "%PY_SYS%"=="" (
    echo.
    echo ====================================================================
    echo  ERROR: Python 3 was not found on your system!
    echo ====================================================================
    echo  To run this application, please install Python:
    echo    1. Download Python 3.10+ from https://www.python.org/downloads/
    echo       (Make sure to check "Add Python to PATH" during installation)
    echo ====================================================================
    echo.
    pause
    exit /b 1
)

REM Check Python Version (Requires 3.10+)
%PY_SYS% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Your installed Python version is older than 3.10.
    echo Please install Python 3.10 or newer from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo   [x] Python 3.10+ verified.

REM 2. Check for uv; install automatically if missing
echo.
echo [2/4] Verifying Astral uv package manager...

SET "UV_CMD="
where uv >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    SET "UV_CMD=uv"
) ELSE (
    %PY_SYS% -m uv --version >nul 2>nul
    IF %ERRORLEVEL% EQU 0 (
        SET "UV_CMD=%PY_SYS% -m uv"
    ) ELSE (
        echo   Downloading and installing uv via pip...
        %PY_SYS% -m pip install --upgrade uv
        where uv >nul 2>nul
        IF %ERRORLEVEL% EQU 0 (
            SET "UV_CMD=uv"
        ) ELSE (
            %PY_SYS% -m uv --version >nul 2>nul
            IF %ERRORLEVEL% EQU 0 (
                SET "UV_CMD=%PY_SYS% -m uv"
            )
        )
    )
)

REM 3. Initialize virtual environment and install dependencies
echo.
echo [3/4] Initializing environment and dependencies...

SET "PY_BIN="

IF NOT "%UV_CMD%"=="" (
    echo   [x] Initializing environment with uv...
    IF NOT EXIST ".venv" (
        %UV_CMD% venv .venv
    )
    echo   [x] Installing / syncing dependencies (duckdb, pandas, python-dateutil)...
    %UV_CMD% pip install "duckdb>=1.0.0" "pandas>=2.0.0" "python-dateutil"
    SET "PY_BIN=.venv\Scripts\python.exe"
) ELSE (
    echo   [!] uv not available, setting up standard venv...
    IF NOT EXIST ".venv" (
        %PY_SYS% -m venv .venv
    )
    SET "PY_BIN=.venv\Scripts\python.exe"
    %PY_BIN% -m pip install "duckdb>=1.0.0" "pandas>=2.0.0" "python-dateutil"
)

REM 4. Run Analytics Pipeline and Serve Dashboard
echo.
echo [4/4] Processing Amazon orders...
"%PY_BIN%" main.py
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: An error occurred while processing orders.
    pause
    exit /b 1
)

echo.
echo Starting local web dashboard server...
echo Your browser will open automatically at http://localhost:8000/dashboard.html
echo Keep this window open while using the dashboard. Press Ctrl+C to close.
echo.

"%PY_BIN%" main.py --serve
pause
