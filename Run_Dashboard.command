#!/bin/bash
# macOS double-click launcher: delegates to run.sh and keeps the window open on errors.
cd "$(dirname "$0")"
chmod +x ./run.sh 2>/dev/null
./run.sh "$@"
status=$?
if [ $status -ne 0 ]; then
    echo ""
    echo "Something went wrong (exit code $status). See the messages above."
    read -p "Press Enter to close..."
fi
exit $status