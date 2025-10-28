#!/usr/bin/env python3
"""
data quality validator for jsonl crawl outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
try:
    from jsonschema import Draft7Validator
except ImportError:  # pragma: no cover - optional dependency
    Draft7Validator = None  # type: ignore[assignment]

from config import get_settings

try:
    import pandera as pa
    from pandera import Column, DataFrameSchema
    from pandera.errors import SchemaErrors
except ImportError:  # pragma: no cover - optional dependency
    pa = None  # type: ignore[assignment]
    Column = None  # type: ignore[assignment]
    DataFrameSchema = None  # type: ignore[assignment]
    SchemaErrors = Exception  # type: ignore[assignment]

HAS_PANDERA = pa is not None
SETTINGS = get_settings()


# validation schemas

JSON_RECORD_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "url": {"type": "string", "minLength": 1},
        "url_normalized": {"type": "string"},
        "depth": {"type": "number"},
        "parent_url": {"type": ["string", "null"]},
        "fragments": {"type": "array"},
        "discovered_at": {"type": ["number", "string", "null"]},
        "queued_at": {"type": ["number", "string", "null"]},
        "crawled_at": {"type": ["number", "string", "null"]},
        "response_time_ms": {"type": ["number", "null"]},
        "status_code": {"type": ["number", "null"]},
        "content_type": {"type": ["string", "null"]},
        "content_length": {"type": ["number", "null"]},
        "title": {"type": ["string", "null"]},
        "links": {"type": "array"},
    },
    "required": ["url", "depth", "status_code", "content_type", "links"],
}


if HAS_PANDERA:
    URL_RECORD_SCHEMA = DataFrameSchema(
        {
            "url": Column(str, checks=pa.Check.str_length(min_value=1)),
            "depth": Column(float, checks=pa.Check.ge(0)),
            "status_code": Column(float, nullable=True),
            "content_type": Column(str, nullable=True),
            "content_length": Column(float, nullable=True, checks=pa.Check.ge(0)),
        },
        coerce=True,
    )
else:
    URL_RECORD_SCHEMA = None


# validation results container

@dataclass
class ValidationResult:
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def report(self) -> None:
        """print validation summary."""
        print("\nData Quality Validation Report")
        status = "PASSED" if self.valid else "FAILED"
        print(f"Status: {status}")

        if self.summary:
            print("\nSummary:")
            for key, value in self.summary.items():
                print(f"  - {key}: {value}")

        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  - {warning}")


# core validation logic

def iterate_records(path: Path) -> Iterable[Dict[str, Any]]:
    """yield parsed json from a jsonl file."""
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue

            try:
                record = json.loads(raw)
                yield record
            except json.JSONDecodeError as exc:
                raise ValueError(f"Line {line_number}: invalid JSON ({exc})") from exc


def _schema_errors(record: Dict[str, Any], validator: Optional[Draft7Validator]) -> List[Tuple[str, str]]:
    if validator is None:
        errors: List[Tuple[str, str]] = []
        required_fields = ["url", "depth", "status_code", "content_type", "links"]
        for field in required_fields:
            if field not in record:
                errors.append(("<root>", f"{field}: field is required"))
        return errors

    return [
        (
            " -> ".join(str(loc) for loc in error.path) or "<root>",
            error.message,
        )
        for error in validator.iter_errors(record)
    ]


def validate_records(path: Path) -> ValidationResult:
    """validate jsonl records against schema and basic rules."""
    result = ValidationResult()
    validator = Draft7Validator(JSON_RECORD_SCHEMA) if Draft7Validator is not None else None
    records: List[Dict[str, Any]] = []

    try:
        for record in iterate_records(path):
            errors = _schema_errors(record, validator)
            if errors:
                for location, message in errors:
                    result.errors.append(f"{location}: {message}")
                result.valid = False
                continue

            # basic sanity checks
            if not isinstance(record.get("links"), list):
                result.errors.append("links: expected list")
                result.valid = False
                continue

            records.append(record)
    except ValueError as exc:
        result.errors.append(str(exc))
        result.valid = False
        return result

    if not records:
        result.errors.append("No valid records were found.")
        result.valid = False
        return result

    # DataFrame-level validation with Pandera when available
    df = pd.DataFrame.from_records(records)
    if HAS_PANDERA and URL_RECORD_SCHEMA is not None:
        try:
            URL_RECORD_SCHEMA.validate(df, lazy=True)
        except SchemaErrors as exc:  # type: ignore[arg-type]
            failure_cases = getattr(exc, "failure_cases", pd.DataFrame())
            result.errors.append(f"Schema validation failed with {len(failure_cases)} issue(s).")
            for _, row in failure_cases.iterrows():
                column = row.get("column", "<unknown>")
                check = row.get("check", "<constraint>")
                failure = row.get("failure_case", "<failure>")
                result.errors.append(f"Column '{column}' failed '{check}': {failure}")
            result.valid = False
    else:
        result.warnings.append("Pandera not available; skipped dataframe schema validation.")

    # Additional integrity checks
    url_counts = Counter(df["url"].astype(str))
    duplicate_urls = [url for url, count in url_counts.items() if count > 1]

    status_codes = Counter(df["status_code"].fillna("null"))
    content_types = Counter(df["content_type"].fillna("null"))

    result.summary = {
        "records": len(df),
        "unique_urls": df["url"].nunique(),
        "duplicates": len(duplicate_urls),
        "status_codes_inspected": len(status_codes),
        "content_types_inspected": len(content_types),
    }

    # warnings
    if duplicate_urls:
        duplicate_percent = (len(duplicate_urls) / len(df) * 100) if len(df) else 0.0
        message = f"Detected {len(duplicate_urls)} duplicate URL(s)."
        if duplicate_percent > SETTINGS.thresholds.duplicate_percent:
            result.errors.append(
                f"{message} Exceeds threshold of {SETTINGS.thresholds.duplicate_percent:.1f}%."
            )
            result.valid = False
        else:
            result.warnings.append(message)

    missing_titles = df["title"].isna().sum() if "title" in df.columns else 0
    if missing_titles:
        result.warnings.append(f"{missing_titles} record(s) missing title.")

    slow_responses = df["response_time_ms"].fillna(0)
    if slow_responses.mean() > SETTINGS.thresholds.response_time_warning_ms:
        result.warnings.append(
            f"Average response time exceeds {SETTINGS.thresholds.response_time_warning_ms:.0f} ms."
        )

    return result


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate JSONL crawl data before analysis.")
    parser.add_argument("input_path", type=Path, help="Path to the JSONL file.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail validation on warnings in addition to errors.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    input_path: Path = args.input_path

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    result = validate_records(input_path)
    result.report()

    if not result.valid:
        return 1

    if args.strict and result.warnings:
        print("\nWarnings treated as failures (--strict).", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
