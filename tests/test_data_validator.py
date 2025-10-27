import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.data_validator import validate_records


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def valid_record(url: str) -> dict:
    return {
        "url": url,
        "url_normalized": url,
        "depth": 1,
        "parent_url": None,
        "fragments": [],
        "discovered_at": 0,
        "queued_at": 0,
        "crawled_at": 0,
        "response_time_ms": 100,
        "status_code": 200,
        "content_type": "text/html",
        "content_length": 1024,
        "title": "Example",
        "links": ["https://example.com/about"],
    }


def test_validate_records_success(tmp_path):
    jsonl_path = tmp_path / "valid.jsonl"
    write_jsonl(jsonl_path, [valid_record("https://example.com"), valid_record("https://example.com/about")])

    result = validate_records(jsonl_path)

    assert result.valid is True
    assert result.summary["records"] == 2
    assert result.summary["duplicates"] == 0


def test_validate_records_detects_schema_errors(tmp_path):
    jsonl_path = tmp_path / "invalid.jsonl"
    write_jsonl(jsonl_path, [{"depth": 1, "links": []}])

    result = validate_records(jsonl_path)

    assert result.valid is False
    assert any("url" in error for error in result.errors)
