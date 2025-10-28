from __future__ import annotations

import json
from pathlib import Path

from analysis.pipeline.master_pipeline import MasterPipeline


def test_load_data_filters_invalid_records(tmp_path: Path) -> None:
    input_file = tmp_path / "input.jsonl"
    input_file.write_text(
        "\n".join(
            [
                json.dumps({"url": "https://example.com", "depth": 1}),
                json.dumps({"foo": "bar"}),
                json.dumps("https://example.org"),
                "not-json",
                "",
            ]
        ),
        encoding="utf-8",
    )

    pipeline = MasterPipeline(str(input_file), output_dir=str(tmp_path / "out"))

    assert pipeline.load_data() is True
    assert pipeline.data == [
        {"url": "https://example.com", "depth": 1},
        {"url": "https://example.org"},
    ]


def test_load_data_missing_file_returns_false(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    pipeline = MasterPipeline(str(missing), output_dir=str(tmp_path / "out"))

    assert pipeline.load_data() is False
    assert pipeline.data == []
