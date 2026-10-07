"""Numbered SQL migrations (#25)."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import text

from app.database import get_engine

logger = logging.getLogger(__name__)
MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "database" / "migrations"


def ensure_migrations_table(conn) -> None:
    conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version TEXT PRIMARY KEY,
              applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """))


def apply_migrations() -> list[str]:
    engine = get_engine()
    applied: list[str] = []
    with engine.begin() as conn:
        ensure_migrations_table(conn)
        existing = {
            r[0] for r in conn.execute(text("SELECT version FROM schema_migrations")).fetchall()
        }
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            ver = path.name
            if ver in existing:
                continue
            sql = path.read_text(encoding="utf-8")
            # split on statements carefully — execute whole file
            conn.execute(text(sql))
            conn.execute(text("INSERT INTO schema_migrations(version) VALUES (:v)"), {"v": ver})
            applied.append(ver)
            logger.info("Applied migration %s", ver)
    return applied
