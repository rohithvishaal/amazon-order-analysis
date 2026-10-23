#!/bin/bash
# ==============================================================================
# Amazon Order Analysis - Cross-Platform Shell Launcher (macOS / Linux)
# ==============================================================================
set -e
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
    echo "❌ Error: Python 3 was not found on your system."
    echo "Please install Python 3.10+ from https://www.python.org/downloads/."
    exit 1
fi

PY_VER=$($PYTHON_SYS -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
PY_COMPAT=$($PYTHON_SYS -c 'import sys; print(1 if sys.version_info >= (3, 10) else 0)' 2>/dev/null)

if [ "$PY_COMPAT" -ne 1 ]; then
    echo "❌ Error: Python $PY_VER detected. Python 3.10 or newer is required."
    exit 1
fi
echo "  ✔ Found Python $PY_VER"

# 2. Check for uv; install automatically if missing
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
    if [ -f ".venv/bin/python" ]; then
        PYTHON_BIN=".venv/bin/python"
    else
        $PYTHON_SYS -m venv .venv
        PYTHON_BIN=".venv/bin/python"
    fi
fi

echo "  ✔ Python environment ready: $PYTHON_BIN"
echo ""

# 4. Launch
echo "📊 [4/4] Running analytics..."
$PYTHON_BIN main.py

echo ""
echo "🌐 Starting web dashboard..."
$PYTHON_BIN main.py --serve "$@"
