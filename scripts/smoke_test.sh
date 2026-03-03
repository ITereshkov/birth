#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/smoke_test.sh
#   LIVE_AVITO=1 ./scripts/smoke_test.sh   # optional live competitor scraping

TMP_OUT_DIR="data/out"
mkdir -p "$TMP_OUT_DIR"

echo "[1/4] Shell syntax checks"
bash -n scripts/build_daily_report.sh scripts/build_recommendations.sh scripts/fetch_competitors_from_avito.sh scripts/import_csv_to_postgres.sh scripts/run_migrations.sh

echo "[2/4] Python compile checks"
python -m compileall src >/dev/null

echo "[3/4] Build reports on template CSVs"
GOAL_STAGE=learning ./scripts/build_daily_report.sh data/templates "$TMP_OUT_DIR/daily_report.smoke.json"
GOAL_STAGE=learning ./scripts/build_recommendations.sh data/templates "$TMP_OUT_DIR/daily_recommendations.smoke.json"

echo "[4/4] Validate output JSON"
python - <<'PY'
import json
from pathlib import Path
rp = Path('data/out/daily_report.smoke.json')
rc = Path('data/out/daily_recommendations.smoke.json')
report = json.loads(rp.read_text(encoding='utf-8'))
reco = json.loads(rc.read_text(encoding='utf-8'))
assert 'ads' in report and len(report['ads']) >= 1
assert 'budget_status' in report
assert 'actions' in reco
assert 'thresholds_used' in reco
print('Smoke checks passed')
PY

if [[ "${LIVE_AVITO:-0}" == "1" ]]; then
  echo "[optional] Live Avito competitor fetch"
  ./scripts/fetch_competitors_from_avito.sh data/templates/ads_own.csv "$TMP_OUT_DIR/competitors_auto.smoke.csv"
  test -s "$TMP_OUT_DIR/competitors_auto.smoke.csv"
  echo "Live fetch produced: $TMP_OUT_DIR/competitors_auto.smoke.csv"
fi

echo "Smoke test completed successfully"
