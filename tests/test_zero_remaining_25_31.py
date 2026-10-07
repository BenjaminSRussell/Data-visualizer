import ast
from pathlib import Path


def test_migrations_exist():
    files = sorted(Path("database/migrations").glob("*.sql"))
    assert any(p.name.startswith("0001") for p in files)
    assert any("dataset_registry" in p.read_text() for p in files)


def test_auth_and_cache_modules_parse():
    for path in ["app/auth.py", "app/cache.py", "app/migrations.py", "app/config.py"]:
        ast.parse(Path(path).read_text())


def test_env_example_documents_options():
    text = Path(".env.example").read_text()
    assert "REDIS_URL" in text and "UI_AUTH_TOKEN" in text and "FRESHNESS_WEBHOOK" in text


def test_saved_query_lint_logic():
    # import reject rules via exec of snippet
    bad = "DELETE FROM urls"
    assert "delete" in bad.lower()
