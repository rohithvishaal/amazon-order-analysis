#!/bin/bash
# ==============================================================================
# Amazon Order Analysis & Intelligence Dashboard - macOS One-Click Launcher
# Double-click this file in Finder to launch the dashboard!
# ==============================================================================

# Ensure script runs from its directory
cd "$(dirname "$0")"

# Include standard user binary directories in PATH
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

echo ""
echo "===================================================================="
echo "  📦 Amazon Order Analysis & Intelligence Dashboard"
echo "===================================================================="
echo ""

# 1. Check for Python
echo "🔍 [1/4] Checking Python installation..."

PYTHON_SYS=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_SYS="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_SYS="python"
fi

if [ -z "$PYTHON_SYS" ]; then
    echo ""
    echo "❌ Missing Dependency: Python 3 was not found on your system."
    echo ""
    echo "To run this application, please install Python 3.10+:"
    echo "  • Download from: https://www.python.org/downloads/"
    echo "  • Or via Homebrew: brew install python"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Python version (>= 3.10 required)
PY_VER=$($PYTHON_SYS -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
PY_COMPAT=$($PYTHON_SYS -c 'import sys; print(1 if sys.version_info >= (3, 10) else 0)' 2>/dev/null)

if [ "$PY_COMPAT" -ne 1 ]; then
    echo ""
    echo "❌ Unsupported Python version: Python $PY_VER detected."
    echo "This dashboard requires Python 3.10 or newer."
    echo "Please update Python from https://www.python.org/downloads/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi
echo "  ✔ Found Python $PY_VER"

# 2. Check for uv; if not present, install it automatically
echo "⚡ [2/4] Verifying uv package manager..."
UV_CMD=""
if command -v uv >/dev/null 2>&1; then
    UV_CMD="uv"
elif $PYTHON_SYS -m uv --version >/dev/null 2>&1; then
    UV_CMD="$PYTHON_SYS -m uv"
else
    echo "  ⬇ 'uv' not found. Installing Astral uv automatically via pip..."
    $PYTHON_SYS -m pip install --upgrade uv || {
        echo "  ⬇ Trying standalone installer..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    }
    if command -v uv >/dev/null 2>&1; then
        UV_CMD="uv"
    elif $PYTHON_SYS -m uv --version >/dev/null 2>&1; then
        UV_CMD="$PYTHON_SYS -m uv"
    fi
fi

# 3. Initialize virtual environment & install dependencies
echo "📦 [3/4] Initializing environment and dependencies..."
PYTHON_BIN=""

if [ -n "$UV_CMD" ]; then
    echo "  ✔ Using uv ($($UV_CMD --version 2>/dev/null | head -n 1))"
    if [ ! -d ".venv" ]; then
        echo "  ⚙ Creating .venv virtual environment with uv..."
        $UV_CMD venv .venv
    fi
    echo "  📥 Syncing project dependencies (duckdb, pandas, python-dateutil)..."
    $UV_CMD pip install "duckdb>=1.0.0" "pandas>=2.0.0" "python-dateutil"
    PYTHON_BIN=".venv/bin/python"
else
    echo "  ⚠️ Continuing without uv. Checking .venv..."
    if [ -f ".venv/bin/python" ]; then
        PYTHON_BIN=".venv/bin/python"
    else
        $PYTHON_SYS -m venv .venv
        PYTHON_BIN=".venv/bin/python"
    fi
fi

echo "  ✔ Python environment ready: $PYTHON_BIN"
echo ""

# 4. Execute Pipeline and Launch Dashboard
echo "📊 [4/4] Processing Amazon orders..."
$PYTHON_BIN main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error processing orders. Please inspect the log above."
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "🌐 Starting local web dashboard server..."
echo "Your default browser will open automatically at http://localhost:8000/dashboard.html"
echo "Keep this terminal window open while using the dashboard. Press Ctrl+C to close."
echo ""

$PYTHON_BIN main.py --serve
