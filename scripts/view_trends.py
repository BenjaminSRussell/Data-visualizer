#!/usr/bin/env python3
"""
View Trends Script

View historical performance trends and comparisons.

Usage:
    python view_trends.py                    # Show summary report
    python view_trends.py --list             # List all snapshots
    python view_trends.py --compare ID1 ID2  # Compare two specific runs
    python view_trends.py --metric METRIC    # Show trend for specific metric
"""

import argparse
import sys
from datetime import datetime

from analysis.tracking import create_tracker


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return iso_timestamp


def print_summary_report(tracker):
    """Print summary report."""
    print("Performance trends summary")

    report = tracker.generate_summary_report()

    if report['status'] == 'insufficient_data':
        print(report['message'])
        print("Run your scraper and store metrics with: python save_metrics.py")
        return

    print(f"Total snapshots: {report['total_snapshots']}")
    latest = report['latest_snapshot']
    print(f"Latest snapshot: {latest['snapshot_id']} ({format_timestamp(latest['timestamp'])})")

    print(report['summary'])

    print("Key metric trends (last 5 runs):")
    for metric_name, trend in report['trends'].items():
        if trend['data_points']:
            first = trend['data_points'][0]['value']
            last = trend['data_points'][-1]['value']

            print(
                f"{metric_name}: first={first:.2f}, latest={last:.2f}, trend={trend['trend']}"
            )


def print_snapshot_list(tracker):
    """Print list of all snapshots."""
    print("Saved metrics snapshots")

    snapshots = tracker.list_snapshots()

    if not snapshots:
        print("No snapshots found.")
        print("Run your scraper and save metrics with: python save_metrics.py")
        return

    print(f"Total snapshots: {len(snapshots)}")

    for snapshot in snapshots:
        metadata_str = ""
        if snapshot.get('metadata'):
            metadata_items = [f"{k}={v}" for k, v in snapshot['metadata'].items()]
            metadata_str = f" ({', '.join(metadata_items)})"

        print(f"{snapshot['snapshot_id']}")
        print(f"Time: {format_timestamp(snapshot['timestamp'])}{metadata_str}")


def print_comparison(tracker, id1, id2):
    """Print detailed comparison between two snapshots."""
    print("Snapshot comparison")

    comparison = tracker.compare_snapshots(id1, id2)

    if not comparison:
        print("Could not load one or both snapshots.")
        return

    print(
        f"Baseline: {comparison['baseline']['snapshot_id']} "
        f"({format_timestamp(comparison['baseline']['timestamp'])})"
    )
    print(
        f"Comparison: {comparison['comparison']['snapshot_id']} "
        f"({format_timestamp(comparison['comparison']['timestamp'])})"
    )

    # Improvements
    improvements = comparison.get('improvements', [])
    if improvements:
        print(f"Improvements ({len(improvements)}):")
        for imp in sorted(improvements, key=lambda x: abs(x['percent']), reverse=True):
            print(f"{imp['metric']}: {imp['percent']:+8.1f}% (delta {imp['delta']:+.2f})")

    # Regressions
    regressions = comparison.get('regressions', [])
    if regressions:
        print(f"Regressions ({len(regressions)}):")
        for reg in sorted(regressions, key=lambda x: abs(x['percent']), reverse=True):
            print(f"{reg['metric']}: {reg['percent']:+8.1f}% (delta {reg['delta']:+.2f})")

    # Stable metrics
    metrics_delta = comparison.get('metrics_delta', {})
    stable = [k for k, v in metrics_delta.items()
              if abs(v['percent_change']) < 1]

    if stable:
        print(f"Stable ({len(stable)} metrics):")
        for metric in stable[:10]:  # Show first 10
            delta = metrics_delta[metric]
            print(f"{metric}: {delta['current']:.2f} (no significant change)")


def print_metric_trend(tracker, metric_name):
    """Print trend for a specific metric."""
    print(f"Trend: {metric_name}")

    trend = tracker.generate_trend_report(metric_name, limit=20)

    if not trend['data_points']:
        print(f"No data found for metric: {metric_name}")
        return

    print(f"Trend direction: {trend['trend']}")
    print(f"Data points: {len(trend['data_points'])}")

    # Print data points
    for i, point in enumerate(trend['data_points'], 1):
        timestamp = format_timestamp(point['timestamp'])
        value = point['value']

        # Calculate change from previous
        if i > 1:
            prev_value = trend['data_points'][i-2]['value']
            if isinstance(value, (int, float)) and isinstance(prev_value, (int, float)):
                change = value - prev_value
                percent = (change / prev_value * 100) if prev_value != 0 else 0
                print(f"{timestamp} {value:8.2f} ({percent:+.1f}%)")
            else:
                print(f"{timestamp} {value}")
        else:
            print(f"{timestamp} {value:8.2f} (baseline)")


def main():
    parser = argparse.ArgumentParser(description='View performance trends')
    parser.add_argument('--list', action='store_true',
                       help='List all saved snapshots')
    parser.add_argument('--compare', nargs=2, metavar=('ID1', 'ID2'),
                       help='Compare two specific snapshots')
    parser.add_argument('--metric', help='Show trend for specific metric')

    args = parser.parse_args()

    tracker = create_tracker()

    if args.list:
        print_snapshot_list(tracker)
    elif args.compare:
        print_comparison(tracker, args.compare[0], args.compare[1])
    elif args.metric:
        print_metric_trend(tracker, args.metric)
    else:
        print_summary_report(tracker)

    return 0


if __name__ == '__main__':
    sys.exit(main())
