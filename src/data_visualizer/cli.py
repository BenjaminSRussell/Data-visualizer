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
    viz_class = load_visualization(args.key)
    viz = viz_class(config=_load_config(args.config))

    output_dir = Path(args.output_dir)
    output_path = viz.run(df, output_dir)
    print(f"Generated visualization at {output_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
