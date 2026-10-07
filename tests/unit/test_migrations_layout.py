"""Versioned migrations layout (#25)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIG = ROOT / "database" / "migrations"


def test_initial_migration_exists():
    files = sorted(MIG.glob("*.sql"))
    assert files, "expected database/migrations/*.sql"
    names = [f.name for f in files]
    assert any(n.startswith("0001_") for n in names)
    initial = next(f for f in files if f.name.startswith("0001_"))
    text = initial.read_text(encoding="utf-8")
    assert "CREATE TABLE" in text.upper()
    assert "urls" in text


def test_manage_has_migrate_command():
    manage = (ROOT / "manage.py").read_text(encoding="utf-8")
    assert "def migrate" in manage
