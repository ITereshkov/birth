#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${1:-DATA}"
OUTPUT_PATH="${2:-data/out/daily_report.json}"
TARGET_CPL="${TARGET_CPL_RUB:-1300}"
DAILY_BUDGET="${DAILY_LIMIT_RUB:-3500}"
MONTHLY_BUDGET="${MONTHLY_LIMIT_RUB:-80000}"

python src/analytics/daily_report.py \
  --data-dir "$DATA_DIR" \
  --target-cpl "$TARGET_CPL" \
  --daily-budget "$DAILY_BUDGET" \
  --monthly-budget "$MONTHLY_BUDGET" \
  --output "$OUTPUT_PATH"

echo "Done: $OUTPUT_PATH"
