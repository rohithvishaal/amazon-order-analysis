#!/bin/bash
# ==============================================================================
# Amazon Order Analysis - Shell Launcher (macOS / Linux)
# ==============================================================================
set -e
cd "$(dirname "$0")"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

echo ""
echo "===================================================================="
echo " Amazon Order Analysis & Intelligence Dashboard"
echo "===================================================================="
echo ""

# 1. Python 3.10+
echo "[1/4] Checking Python..."
PYTHON_SYS=""
for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1 && \
       "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        PYTHON_SYS="$cand"
        break
    fi
done
if [ -z "$PYTHON_SYS" ]; then
    echo "ERROR: Python 3.10+ was not found. Install it from https://www.python.org/downloads/"
    exit 1
fi
echo "  OK: $($PYTHON_SYS --version)"

# 2. uv (fast package manager) + virtual environment + dependencies
echo "[2/4] Setting up environment and dependencies with uv..."
PYTHON_BIN=".venv/bin/python"

find_uv() {
    if command -v uv >/dev/null 2>&1; then UV_CMD=(uv); return 0; fi
    if "$PYTHON_SYS" -m uv --version >/dev/null 2>&1; then UV_CMD=("$PYTHON_SYS" -m uv); return 0; fi
    return 1
}

if ! find_uv; then
    echo "  uv not found - installing it (one time)..."
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh || true
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh || true
    fi
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    if ! find_uv; then
        # Last resort: use pip ONLY to bootstrap uv itself
        "$PYTHON_SYS" -m pip install --user --upgrade uv \
            || "$PYTHON_SYS" -m pip install --user --break-system-packages --upgrade uv || true
        find_uv || { echo "ERROR: could not install uv. See https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
    fi
fi
echo "  OK: $("${UV_CMD[@]}" --version)"

# Recreate a broken venv
if [ -d ".venv" ] && [ ! -x "$PYTHON_BIN" ]; then rm -rf .venv; fi
"${UV_CMD[@]}" sync
echo "  OK: dependencies installed"

# 3. Chart.js (needed for the graphs) - downloaded directly if not present
echo "[3/4] Checking Chart.js..."
"$PYTHON_BIN" -m src.chartjs || echo "  WARN: could not download Chart.js - graphs will not render"

# 4. Build dashboard and serve (main.py --serve builds the dashboard first)
echo "[4/4] Starting dashboard at http://localhost:8000/dashboard.html (Ctrl+C to stop)"
exec "$PYTHON_BIN" main.py --serve "$@"
