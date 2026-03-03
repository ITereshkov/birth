-- Core schema for Avito AI Copilot MVP

CREATE TABLE IF NOT EXISTS ads_own (
    id BIGSERIAL PRIMARY KEY,
    ad_id TEXT NOT NULL UNIQUE,
    subject TEXT NOT NULL,
    region TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    lesson_format TEXT,
    price_rub NUMERIC(10,2),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ads_own_daily_metrics (
    id BIGSERIAL PRIMARY KEY,
    ad_id TEXT NOT NULL REFERENCES ads_own(ad_id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    impressions INTEGER NOT NULL DEFAULT 0,
    views INTEGER NOT NULL DEFAULT 0,
    contacts INTEGER NOT NULL DEFAULT 0,
    favorites INTEGER NOT NULL DEFAULT 0,
    spend_rub NUMERIC(12,2) NOT NULL DEFAULT 0,
    bid_rub NUMERIC(10,2),
    avg_position NUMERIC(6,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(ad_id, metric_date)
);

CREATE TABLE IF NOT EXISTS ad_changes_log (
    id BIGSERIAL PRIMARY KEY,
    ad_id TEXT NOT NULL REFERENCES ads_own(ad_id) ON DELETE CASCADE,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_source TEXT NOT NULL DEFAULT 'manual'
);

CREATE INDEX IF NOT EXISTS idx_ads_own_daily_metrics_date
    ON ads_own_daily_metrics(metric_date);

CREATE INDEX IF NOT EXISTS idx_ad_changes_log_ad_id_changed_at
    ON ad_changes_log(ad_id, changed_at DESC);
