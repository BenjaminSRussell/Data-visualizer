from __future__ import annotations

import json
from pathlib import Path

from analysis.load_urls import execute, validate


def test_execute_handles_mixed_entries(tmp_path: Path) -> None:
    input_file = tmp_path / "urls.jsonl"
    input_file.write_text(
        "\n".join(
            [
                json.dumps({"url": "https://example.com"}),
                json.dumps("https://example.org"),
                json.dumps({"url": ""}),
                "invalid",
            ]
        ),
        encoding="utf-8",
    )

    records = execute(str(input_file))

    assert records == [
        {"url": "https://example.com"},
        {"url": "https://example.org"},
    ]


def test_execute_missing_file(tmp_path: Path) -> None:
    input_file = tmp_path / "missing.jsonl"
    assert execute(str(input_file)) == []


def test_validate_reports_errors(tmp_path: Path) -> None:
    input_file = tmp_path / "urls.jsonl"
    input_file.write_text(
        "\n".join(
            [
                json.dumps({"url": "https://example.com"}),
                "invalid",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = validate(str(input_file))

    assert result["valid"] is True
    assert result["total_lines"] == 2
    assert result["valid_urls"] == 1
    assert "Line 2: Invalid JSON" in result["errors"]
