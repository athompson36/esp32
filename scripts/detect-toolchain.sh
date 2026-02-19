#!/usr/bin/env bash
# Detect build toolchain by presence of known project files.
# Usage: detect-toolchain.sh [path]
# Output: platformio | idf | cargo | unknown
# Used by orchestrator/Cursor to suggest correct build/flash commands. See FEATURE_ROADMAP L14.
set -e
DIR="${1:-.}"
[ -n "$DIR" ] && [ ! -d "$DIR" ] && echo "unknown" && exit 0
if [ -f "$DIR/platformio.ini" ]; then
  echo "platformio"
elif [ -f "$DIR/idf.py" ] || { [ -f "$DIR/CMakeLists.txt" ] && grep -q "idf_component\|idf_project" "$DIR/CMakeLists.txt" 2>/dev/null; }; then
  echo "idf"
elif [ -f "$DIR/Cargo.toml" ]; then
  echo "cargo"
else
  echo "unknown"
fi
