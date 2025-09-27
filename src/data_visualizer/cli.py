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
    parser.add_argument(
        "--describe",
        action="store_true",
        help="Describe requirements for a specific visualization.",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Show execution plan without running visualization.",
    )
    parser.add_argument(
        "--preset",
        help="Use a named preset configuration file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned operations without rendering.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable performance profiling.",
    )
    return parser.parse_args(argv)


def _load_config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def _load_preset(preset_name: str) -> dict[str, Any]:
    """Load a named preset configuration."""
    preset_path = Path(f"presets/{preset_name}.json")
    if not preset_path.exists():
        # Try alternate locations
        preset_path = Path(f"{preset_name}.json")
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset '{preset_name}' not found. Looked in: presets/{preset_name}.json, {preset_name}.json")

    with open(preset_path, "r", encoding="utf-8") as f:
        preset_data = json.load(f)

    return preset_data


def describe_visualization(viz_key: str) -> None:
    """Describe requirements and configuration options for a visualization."""
    try:
        viz_class = load_visualization(viz_key)
        metadata = viz_class.metadata

        print(f"📊 {metadata.title}")
        print(f"Type: {metadata.insight_type}")
        print(f"Description: {metadata.description}")
        print(f"Tags: {', '.join(metadata.tags)}")
        print(f"Example: {metadata.example_url}")
        print()

        # Schema requirements
        schema_requirements = {
            "trend_line_chart": {
                "min_columns": 2,
                "description": "Requires at least 2 columns (x-axis, y-axis)",
                "example_columns": ["date", "value"],
                "config_options": ["value_columns", "rolling_window", "anomaly_detection", "export_trends"]
            },
            "comparison_grouped_bar": {
                "min_columns": 3,
                "description": "Requires exactly 3 columns (group, category, value)",
                "example_columns": ["region", "product", "sales"],
                "config_options": ["aggregation", "sort_by", "chart_type", "normalize", "show_error_bars", "export_summary"]
            },
            "distribution_violin": {
                "min_columns": 2,
                "description": "Requires at least 2 columns (category, numeric_value)",
                "example_columns": ["segment", "score"],
                "config_options": ["swarm_overlay", "log_scale", "outlier_detection", "export_stats", "normality_tests"]
            },
            "relationship_cluster_scatter": {
                "min_columns": 2,
                "description": "Requires at least 2 numeric columns for clustering",
                "example_columns": ["feature1", "feature2", "feature3"],
                "config_options": ["algorithm", "n_clusters", "detect_outliers", "stability_analysis", "export_analysis"]
            },
            "comparison_heatmap": {
                "min_columns": 3,
                "description": "Requires 3 columns (row_category, column_category, value)",
                "example_columns": ["region", "product", "sales"],
                "config_options": ["aggregation", "cluster_rows", "statistical_testing", "export_rankings"]
            },
            "hierarchy_treemap": {
                "min_columns": 2,
                "description": "Requires at least 2 columns (hierarchy + value)",
                "example_columns": ["region", "country", "city", "population"],
                "config_options": ["threshold_filter", "variance_coloring", "pattern_detection", "export_hierarchy"]
            },
            "segmentation_parallel_sets": {
                "min_columns": 2,
                "description": "Requires at least 2 categorical columns for flow analysis",
                "example_columns": ["channel", "plan", "status", "count"],
                "config_options": ["conversion_analysis", "drop_off_analysis", "export_funnel"]
            }
        }

        if viz_key in schema_requirements:
            req = schema_requirements[viz_key]
            print("📋 Requirements:")
            print(f"  Minimum columns: {req['min_columns']}")
            print(f"  Description: {req['description']}")
            print(f"  Example columns: {', '.join(req['example_columns'])}")
            print()
            print("⚙️  Key configuration options:")
            for option in req['config_options']:
                print(f"  - {option}")

    except KeyError:
        print(f"❌ Visualization '{viz_key}' not found")
        print("Use --list to see available visualizations")


def plan_execution(dataset_path: Path, viz_key: str, config: dict) -> None:
    """Show execution plan without running."""
    print("📋 Execution Plan")
    print(f"Dataset: {dataset_path}")
    print(f"Visualization: {viz_key}")
    print(f"Configuration: {json.dumps(config, indent=2) if config else 'Default'}")
    print()

    if dataset_path.exists():
        df = pd.read_csv(dataset_path, nrows=5)  # Just preview
        print(f"📊 Dataset Preview ({dataset_path.stat().st_size:,} bytes):")
        print(f"  Shape: {df.shape[0]}+ rows × {df.shape[1]} columns")
        print(f"  Columns: {', '.join(df.columns)}")
        print(f"  Column types: {dict(df.dtypes)}")
        print()

        # Validate schema
        validation_errors = validate_dataset_schema(df, viz_key)
        if validation_errors:
            print("⚠️  Validation Issues:")
            for error in validation_errors:
                print(f"  - {error}")
        else:
            print("✅ Dataset validation passed")

    print()
    print("🎯 Planned Operations:")
    print("  1. Load and validate dataset")
    print("  2. Apply data preparation")
    print("  3. Render visualization")
    print("  4. Save output to specified directory")


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
        },
        "comparison_heatmap": {
            "min_columns": 3,
            "description": "Requires 3 columns (row_category, column_category, value)",
            "column_types": {"numeric_columns": 1}  # At least 1 numeric column for values
        },
        "hierarchy_treemap": {
            "min_columns": 2,
            "description": "Requires at least 2 columns (hierarchy + value)",
            "column_types": {"numeric_columns": 1}  # At least 1 numeric column for sizing
        },
        "segmentation_parallel_sets": {
            "min_columns": 2,
            "description": "Requires at least 2 categorical columns for flow analysis",
            "column_types": {}  # No strict numeric requirements (can use counts)
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
    import time
    start_time = time.time()

    args = parse_args(argv)

    # Handle list command
    if args.list:
        print("📊 Available Visualizations:")
        print("=" * 80)
        for metadata in list_visualizations():
            tag_blob = ", ".join(metadata.tags)
            print(f"{metadata.key:>25} | {metadata.title:20} | {metadata.insight_type:12} | {tag_blob}")
        return 0

    # Handle describe command
    if args.describe:
        if not args.key:
            print("❌ Provide a visualization key to describe (e.g., --key comparison_grouped_bar)")
            print("Use --list to see available visualizations")
            return 1
        describe_visualization(args.key)
        return 0

    # Main execution path
    if not args.dataset or not args.key:
        print("Provide both a dataset path and visualization key, or use --list.")
        return 1

    # Load configuration (preset takes precedence)
    if args.preset:
        try:
            config = _load_preset(args.preset)
            # Allow command-line config to override preset
            if args.config:
                preset_config = config
                cli_config = _load_config(args.config)
                config = {**preset_config, **cli_config}  # CLI overrides preset
        except Exception as e:
            print(f"❌ Failed to load preset '{args.preset}': {e}")
            return 1
    else:
        config = _load_config(args.config)

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    # Handle plan command
    if args.plan:
        plan_execution(dataset_path, args.key, config)
        return 0

    # Handle dry-run
    if args.dry_run:
        print("🏃 Dry Run Mode")
        print("=" * 40)
        plan_execution(dataset_path, args.key, config)
        print("\n💡 This was a dry run. Add actual execution by removing --dry-run")
        return 0

    # Load and validate dataset
    load_start = time.time()
    df = pd.read_csv(dataset_path, sep=args.separator, encoding=args.encoding)
    load_time = time.time() - load_start

    if args.profile:
        print(f"⏱️  Data loading: {load_time:.3f}s")

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

    # Create and run visualization
    prep_start = time.time()
    viz_class = load_visualization(args.key)
    viz = viz_class(config=config)
    prep_time = time.time() - prep_start

    if args.profile:
        print(f"⏱️  Preparation: {prep_time:.3f}s")

    render_start = time.time()
    output_dir = Path(args.output_dir)
    output_path = viz.run(df, output_dir)
    render_time = time.time() - render_start

    total_time = time.time() - start_time

    # Generate run manifest
    manifest = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset": str(dataset_path),
        "visualization": args.key,
        "output": str(output_path),
        "config": config,
        "dataset_shape": list(df.shape),
        "performance": {
            "load_time": round(load_time, 3),
            "prep_time": round(prep_time, 3),
            "render_time": round(render_time, 3),
            "total_time": round(total_time, 3)
        }
    }

    # Save manifest
    manifest_path = output_path.with_name(output_path.stem + '_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Generated visualization at {output_path}")
    if args.profile:
        print(f"⏱️  Rendering: {render_time:.3f}s")
        print(f"⏱️  Total time: {total_time:.3f}s")
        print(f"📋 Run manifest: {manifest_path}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
