#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${1:-DATA}"
OUTPUT_PATH="${2:-data/out/daily_recommendations.json}"
TARGET_CPL="${TARGET_CPL_RUB:-1300}"
DAILY_BUDGET="${DAILY_LIMIT_RUB:-3500}"
MONTHLY_BUDGET="${MONTHLY_LIMIT_RUB:-80000}"
CONVERSION_TARGET="${CONVERSION_TARGET:-0.08}"
GOAL_STAGE="${GOAL_STAGE:-learning}"
CPV_POLICY_PATH="${CPV_POLICY_PATH:-configs/cpv_policy.json}"

python -m src.analytics.recommendations \
  --data-dir "$DATA_DIR" \
  --target-cpl "$TARGET_CPL" \
  --daily-budget "$DAILY_BUDGET" \
  --monthly-budget "$MONTHLY_BUDGET" \
  --conversion-target "$CONVERSION_TARGET" \
  --stage "$GOAL_STAGE" \
  --policy "$CPV_POLICY_PATH" \
  --output "$OUTPUT_PATH"

echo "Done: $OUTPUT_PATH"
