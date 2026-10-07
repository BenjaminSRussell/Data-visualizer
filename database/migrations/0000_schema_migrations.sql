-- Migration 0000_schema_migrations

-- Schema migrations bookkeeping (idempotent)
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(64) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
