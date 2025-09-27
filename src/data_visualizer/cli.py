"""Command line interface for running bundled visualizations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from . import list_visualizations, load_visualization


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run data visualizations on a dataset.")
    parser.add_argument("dataset", nargs="?", help="Path to the dataset (CSV by default).")
    parser.add_argument("key", nargs="?", help="Visualization key to run (see --list).")
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory where generated assets will be stored.",
    )
    parser.add_argument(
        "--config",
        help="Optional JSON file with configuration passed to the visualization instance.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available visualizations and exit.",
    )
    parser.add_argument(
        "--separator",
        default=",",
        help="Dataset delimiter (default: ',').",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Dataset encoding (default: utf-8).",
    )
    return parser.parse_args(argv)


def _load_config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def validate_dataset_schema(df: pd.DataFrame, viz_key: str) -> list[str]:
    """Validate dataset schema against visualization requirements.

    Returns list of validation errors, empty if valid.
    """
    errors = []

    if df.empty:
        errors.append("Dataset is empty - no rows to visualize")
        return errors

    # Define schema requirements for each visualization type
    schema_requirements = {
        "trend_line_chart": {
            "min_columns": 2,
            "description": "Requires at least 2 columns (x-axis, y-axis)",
            "column_types": {"numeric_columns": 1}  # At least 1 numeric column
        },
        "comparison_grouped_bar": {
            "min_columns": 3,
            "description": "Requires exactly 3 columns (group, category, value)",
            "column_types": {"numeric_columns": 1}  # At least 1 numeric column for values
        },
        "distribution_violin": {
            "min_columns": 2,
            "description": "Requires at least 2 columns (category, numeric_value)",
            "column_types": {"numeric_columns": 1}  # At least 1 numeric column
        },
        "relationship_cluster_scatter": {
            "min_columns": 2,
            "description": "Requires at least 2 numeric columns for clustering",
            "column_types": {"numeric_columns": 2}  # At least 2 numeric columns
        }
    }

    # Get requirements for this visualization
    requirements = schema_requirements.get(viz_key)
    if not requirements:
        # Unknown visualization, skip validation
        return errors

    # Check minimum columns
    if df.shape[1] < requirements["min_columns"]:
        errors.append(
            f"Dataset has {df.shape[1]} columns but {viz_key} requires "
            f"at least {requirements['min_columns']} columns. "
            f"{requirements['description']}"
        )

    # Check column types
    numeric_cols = df.select_dtypes(include=['number']).columns
    required_numeric = requirements["column_types"].get("numeric_columns", 0)

    if len(numeric_cols) < required_numeric:
        errors.append(
            f"Dataset has {len(numeric_cols)} numeric columns but {viz_key} requires "
            f"at least {required_numeric} numeric columns. "
            f"Found numeric columns: {list(numeric_cols)}"
        )

    # Check for all-null columns
    null_columns = df.columns[df.isnull().all()].tolist()
    if null_columns:
        errors.append(f"Dataset contains columns with all null values: {null_columns}")

    # Check for duplicate column names
    if len(df.columns) != len(set(df.columns)):
        duplicates = df.columns[df.columns.duplicated()].tolist()
        errors.append(f"Dataset contains duplicate column names: {duplicates}")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list:
        for metadata in list_visualizations():
            tag_blob = ", ".join(metadata.tags)
            print(f"{metadata.key:>25} | {metadata.title:20} | {metadata.insight_type:12} | {tag_blob}")
        return 0

    if not args.dataset or not args.key:
        print("Provide both a dataset path and visualization key, or use --list.")
        return 1

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path, sep=args.separator, encoding=args.encoding)

    # Validate dataset schema before proceeding
    validation_errors = validate_dataset_schema(df, args.key)
    if validation_errors:
        print("❌ Dataset validation failed:")
        for i, error in enumerate(validation_errors, 1):
            print(f"  {i}. {error}")
        print(f"\nDataset summary:")
        print(f"  - Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"  - Columns: {list(df.columns)}")
        print(f"  - Column types: {dict(df.dtypes)}")
        return 1

    viz_class = load_visualization(args.key)
    viz = viz_class(config=_load_config(args.config))

    output_dir = Path(args.output_dir)
    output_path = viz.run(df, output_dir)
    print(f"✅ Generated visualization at {output_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
