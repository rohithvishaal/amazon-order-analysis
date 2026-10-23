#!/bin/bash
# ==============================================================================
# Amazon Order Analysis & Intelligence Dashboard - macOS One-Click Launcher
# Double-click this file in Finder to launch the dashboard!
# ==============================================================================

# Ensure script runs from its directory
cd "$(dirname "$0")"

echo ""
echo "===================================================================="
echo "  📦 Launching Amazon Order Analysis & Intelligence Dashboard...   "
echo "===================================================================="
echo ""

# Find Python / venv
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
elif command -v uv >/dev/null 2>&1; then
    echo "Creating virtual environment using uv..."
    uv venv
    uv pip install pandas duckdb numpy python-dateutil
    PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "❌ Error: Python 3 was not found on your system."
    echo "Please install Python 3 from https://python.org or uv from https://astral.sh/uv"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Running analytics pipeline..."
$PYTHON_BIN main.py

echo ""
echo "🌐 Starting local web dashboard server..."
echo "Your default browser will open automatically."
echo "Keep this window open while viewing. Press Ctrl+C to stop."
echo ""

$PYTHON_BIN main.py --serve

