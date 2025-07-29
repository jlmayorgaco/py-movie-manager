#!/bin/bash

# === CONFIG ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MAIN_SCRIPT="main.py"
CONFIG_PATH="config/config.sandbox.json"
PYTHON_BIN="python"

# === STEP 1: Confirm __RAW__ folder exists and contains movie folders ===
RAW_DIR="$PROJECT_DIR/__sandbox__/__RAW__"
echo "🔍 Checking RAW directory structure at: $RAW_DIR"
if [ ! -d "$RAW_DIR" ]; then
    echo "❌ ERROR: RAW directory not found!"
    exit 1
fi

RAW_COUNT=$(find "$RAW_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
if [ "$RAW_COUNT" -eq 0 ]; then
    echo "❌ ERROR: No genre folders found in RAW directory."
    exit 1
else
    echo "✅ RAW has $RAW_COUNT movie collection folders."
fi

# === STEP 2: Dry run and check for logs ===
echo ""
echo "🚀 Running dry-run in sandbox mode..."
$PYTHON_BIN "$MAIN_SCRIPT" --sandbox --os=synology > dry_run.log 2>&1

echo ""
echo "📄 Extracting relevant log messages:"
echo "---------------------------------------"
grep -E "Would (copy|delete|create directory):" dry_run.log | tee extracted.log

COPY_COUNT=$(grep -c "Would copy" dry_run.log)
DELETE_COUNT=$(grep -c "Would delete" dry_run.log)
TEMP_CREATED=$(grep -c "__TMM_TEMP__" dry_run.log)

echo ""
if [ "$COPY_COUNT" -gt 0 ]; then
    echo "✅ Copy actions detected: $COPY_COUNT"
else
    echo "❌ No copy actions detected!"
fi

if [ "$DELETE_COUNT" -gt 0 ]; then
    echo "✅ Delete actions detected: $DELETE_COUNT"
else
    echo "❌ No delete actions detected!"
fi

if [ "$TEMP_CREATED" -gt 0 ]; then
    echo "✅ TEMP directory __TMM_TEMP__ is being created/used."
else
    echo "❌ TEMP directory not mentioned in logs!"
fi

# === Summary ===
echo ""
echo "🔚 Summary:"
if [ "$COPY_COUNT" -gt 0 ] && [ "$DELETE_COUNT" -gt 0 ] && [ "$TEMP_CREATED" -gt 0 ]; then
    echo "🎉 All checks passed. You are ready to go LIVE!"
else
    echo "⚠️ One or more checks failed. Please review dry_run.log"
fi
