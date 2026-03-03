#!/usr/bin/env bash
set -euo pipefail

OWN_ADS_CSV="${1:-data/inbox/ads_own.csv}"
OUTPUT="${2:-DATA/competitors_auto.csv}"
TOP_N="${TOP_N:-20}"
DELAY_S="${DELAY_S:-1.5}"

python -m src.collectors.avito_competitors \
  --own-ads "$OWN_ADS_CSV" \
  --output "$OUTPUT" \
  --top-n "$TOP_N" \
  --delay-s "$DELAY_S"

echo "Done: $OUTPUT"
