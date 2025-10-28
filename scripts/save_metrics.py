#!/usr/bin/env python3
"""
Save Metrics Script

Quick script to save current analysis results to metrics history.
Run this after each scraper run to track performance over time.

Usage:
    python save_metrics.py [run_id] [--metadata key=value ...]
"""

import argparse
import json
import sys
from pathlib import Path

from analysis.tracking import create_tracker


def main():
    parser = argparse.ArgumentParser(description='Save metrics snapshot')
    parser.add_argument('run_id', nargs='?', help='Optional run identifier')
    parser.add_argument('--metadata', nargs='*', help='Metadata in key=value format')
    parser.add_argument('--results-file', default='output/summary.json',
                       help='Path to analysis results JSON')

    args = parser.parse_args()

    # Load analysis results
    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f"Results file not found: {args.results_file}")
        print("Run the analysis first to generate results.")
        return 1

    with open(results_path, 'r') as f:
        analysis_results = json.load(f)

    # Parse metadata
    metadata = {}
    if args.metadata:
        for item in args.metadata:
            if '=' in item:
                key, value = item.split('=', 1)
                metadata[key] = value

    # Create tracker and save snapshot
    tracker = create_tracker()
    key_metrics = tracker.extract_key_metrics(analysis_results)

    snapshot_id = tracker.save_snapshot(
        metrics=key_metrics,
        run_id=args.run_id,
        metadata=metadata
    )

    print(f"Metrics saved with ID: {snapshot_id}")

    # Show quick comparison if there's a previous snapshot
    snapshots = tracker.list_snapshots()
    if len(snapshots) >= 2:
        print("Quick comparison with previous run:")
        comparison = tracker.compare_snapshots(
            snapshots[-2]['snapshot_id'],
            snapshots[-1]['snapshot_id']
        )

        improvements = comparison.get('improvements', [])
        regressions = comparison.get('regressions', [])

        print(f"Improvements: {len(improvements)}")
        if improvements:
            for imp in improvements[:3]:
                print(f"{imp['metric']}: {imp['percent']:+.1f}%")

        print(f"Regressions: {len(regressions)}")
        if regressions:
            for reg in regressions[:3]:
                print(f"{reg['metric']}: {reg['percent']:+.1f}%")

    print("Tip: Run 'python view_trends.py' to see historical trends")

    return 0


if __name__ == '__main__':
    sys.exit(main())
