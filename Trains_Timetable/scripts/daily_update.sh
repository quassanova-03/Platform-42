#!/bin/bash

# Move to the project directory
cd "$(dirname "$0")/.."

echo "========================================"
echo "       TRAIN TRACKER DAILY UPDATE"
echo "========================================"

echo ""
echo "[$(TZ=Asia/Kolkata date)] Validating dataset..."

python3 scripts/validator.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Dataset validation failed."
    echo "Database update cancelled."
    echo "[$(TZ=Asia/Kolkata date)] Pipeline stopped."
    exit 1
fi

echo ""
echo "[$(TZ=Asia/Kolkata date)] Dataset validation passed."

echo ""
echo "[$(TZ=Asia/Kolkata date)] Updating database..."

python3 scripts/database.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Database update failed."
    echo "Report generation cancelled."
    echo "[$(TZ=Asia/Kolkata date)] Pipeline stopped."
    exit 1
fi

echo ""
echo "[$(TZ=Asia/Kolkata date)] Database update completed."

echo ""
echo "[$(TZ=Asia/Kolkata date)] Generating report..."

python3 scripts/report_v2.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Report generation failed."
    echo "[$(TZ=Asia/Kolkata date)] Pipeline stopped."
    exit 1
fi

echo ""
echo "[$(TZ=Asia/Kolkata date)] Daily update completed successfully."
echo "========================================"
