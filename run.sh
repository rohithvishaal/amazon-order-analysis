#!/bin/bash
# ==============================================================================
# Amazon Order Analysis - Cross-Platform Shell Launcher (macOS / Linux)
# ==============================================================================
cd "$(dirname "$0")"

PYTHON_BIN="python3"
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
fi

$PYTHON_BIN main.py --serve "$@"

