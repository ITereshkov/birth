#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set"
  echo "Example: postgresql://avito:avito@localhost:5432/avito_copilot"
  exit 1
fi

ADS_CSV="${1:-data/inbox/ads_own.csv}"
METRICS_CSV="${2:-data/inbox/ads_own_daily_metrics.csv}"

if [[ ! -f "$ADS_CSV" ]]; then
  echo "ERROR: file not found: $ADS_CSV"
  exit 1
fi

if [[ ! -f "$METRICS_CSV" ]]; then
  echo "ERROR: file not found: $METRICS_CSV"
  exit 1
fi

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<SQL
CREATE TEMP TABLE tmp_ads_own (
  ad_id TEXT,
  subject TEXT,
  region TEXT,
  title TEXT,
  description TEXT,
  lesson_format TEXT,
  price_rub NUMERIC(10,2),
  is_active BOOLEAN
);

CREATE TEMP TABLE tmp_ads_own_daily_metrics (
  ad_id TEXT,
  metric_date DATE,
  impressions INTEGER,
  views INTEGER,
  contacts INTEGER,
  favorites INTEGER,
  spend_rub NUMERIC(12,2),
  bid_rub NUMERIC(10,2),
  avg_position NUMERIC(6,2)
);

\copy tmp_ads_own FROM '$ADS_CSV' WITH (FORMAT csv, HEADER true)
\copy tmp_ads_own_daily_metrics FROM '$METRICS_CSV' WITH (FORMAT csv, HEADER true)

INSERT INTO ads_own (ad_id, subject, region, title, description, lesson_format, price_rub, is_active)
SELECT ad_id, subject, region, title, description, lesson_format, price_rub, COALESCE(is_active, true)
FROM tmp_ads_own
ON CONFLICT (ad_id) DO UPDATE SET
  subject = EXCLUDED.subject,
  region = EXCLUDED.region,
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  lesson_format = EXCLUDED.lesson_format,
  price_rub = EXCLUDED.price_rub,
  is_active = EXCLUDED.is_active,
  updated_at = NOW();

INSERT INTO ads_own_daily_metrics (
  ad_id, metric_date, impressions, views, contacts, favorites, spend_rub, bid_rub, avg_position
)
SELECT
  ad_id,
  metric_date,
  COALESCE(impressions, 0),
  COALESCE(views, 0),
  COALESCE(contacts, 0),
  COALESCE(favorites, 0),
  COALESCE(spend_rub, 0),
  bid_rub,
  avg_position
FROM tmp_ads_own_daily_metrics
ON CONFLICT (ad_id, metric_date) DO UPDATE SET
  impressions = EXCLUDED.impressions,
  views = EXCLUDED.views,
  contacts = EXCLUDED.contacts,
  favorites = EXCLUDED.favorites,
  spend_rub = EXCLUDED.spend_rub,
  bid_rub = EXCLUDED.bid_rub,
  avg_position = EXCLUDED.avg_position;
SQL

echo "Import completed: $ADS_CSV + $METRICS_CSV"
