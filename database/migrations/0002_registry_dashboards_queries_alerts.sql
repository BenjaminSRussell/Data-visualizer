-- Dataset registry, dashboards, saved queries, freshness alerts (#28–#31)

CREATE TABLE IF NOT EXISTS dataset_registry (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  source_uri TEXT,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  row_count BIGINT DEFAULT 0,
  schema_hash TEXT,
  sla_hours INTEGER DEFAULT 168
);

CREATE TABLE IF NOT EXISTS dashboards (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  layout_json JSONB NOT NULL DEFAULT '{}',
  owner TEXT DEFAULT 'local',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS saved_queries (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  sql TEXT NOT NULL,
  owner TEXT DEFAULT 'local',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS freshness_alerts (
  id SERIAL PRIMARY KEY,
  dataset_name TEXT NOT NULL,
  fired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  cleared_at TIMESTAMPTZ,
  payload_json JSONB
);

CREATE UNIQUE INDEX IF NOT EXISTS freshness_alerts_open_uidx
  ON freshness_alerts (dataset_name)
  WHERE cleared_at IS NULL;
