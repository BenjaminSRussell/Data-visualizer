"""
Historical Metrics Tracker

Purpose: Track scraper performance metrics over time to identify trends,
         improvements, and regressions.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class MetricsTracker:
    """Track and store scraper performance metrics over time."""

    def __init__(self, history_dir: str = "metrics_history"):
        self.history_dir = Path(history_dir)
        self.snapshots_dir = self.history_dir / "snapshots"
        self.trends_dir = self.history_dir / "trends"
        self.reports_dir = self.history_dir / "reports"

        # Ensure directories exist
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.trends_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, metrics: Dict, run_id: Optional[str] = None,
                     metadata: Optional[Dict] = None) -> str:
        """
        Save a snapshot of current metrics.

        Args:
            metrics: Dictionary of metrics to save
            run_id: Optional identifier for this run
            metadata: Optional metadata (git commit, config, etc.)

        Returns:
            Snapshot ID (timestamp-based)
        """
        timestamp = datetime.now()
        snapshot_id = run_id or timestamp.strftime("%Y%m%d_%H%M%S")

        snapshot = {
            "snapshot_id": snapshot_id,
            "timestamp": timestamp.isoformat(),
            "metadata": metadata or {},
            "metrics": metrics
        }

        # Save snapshot
        filename = f"{snapshot_id}.json"
        filepath = self.snapshots_dir / filename

        with open(filepath, 'w') as f:
            json.dump(snapshot, f, indent=2)

        print(f" Saved metrics snapshot: {filename}")
        return snapshot_id

    def extract_key_metrics(self, analysis_results: Dict) -> Dict:
        """
        Extract key performance metrics from full analysis results.

        Args:
            analysis_results: Full results from analyzer pipeline

        Returns:
            Dictionary of key metrics for tracking
        """
        key_metrics = {
            # Basic counts
            "total_urls": 0,
            "unique_urls": 0,
            "total_links": 0,

            # Performance metrics
            "crawl_duration_seconds": 0,
            "urls_per_second": 0,
            "avg_response_time_ms": 0,

            # Quality metrics
            "data_quality_score": 0,
            "extraction_success_rate": 0,
            "error_rate": 0,

            # Efficiency metrics
            "duplication_rate": 0,
            "storage_efficiency": 0,
            "depth_efficiency": 0,

            # Coverage metrics
            "max_depth_reached": 0,
            "avg_depth": 0,
            "unique_domains": 0,

            # Link graph metrics
            "graph_density": 0,
            "isolated_components": 0,
            "largest_component_percent": 0,

            # Content metrics
            "pages_with_title": 0,
            "pages_with_links": 0,
            "avg_links_per_page": 0
        }

        # Extract from statistical analysis
        if 'statistical' in analysis_results:
            stats = analysis_results['statistical']
            if 'summary_stats' in stats:
                summary = stats['summary_stats']
                key_metrics['total_urls'] = summary.get('total_urls', 0)
                key_metrics['avg_depth'] = summary.get('depth_mean', 0)
                key_metrics['max_depth_reached'] = summary.get('depth_max', 0)
                key_metrics['avg_links_per_page'] = summary.get('outbound_links_mean', 0)

        # Extract from data quality analysis
        if 'data_quality' in analysis_results:
            quality = analysis_results['data_quality']
            key_metrics['data_quality_score'] = quality.get('overall_quality_score', 0)

            if 'fragment_inflation' in quality:
                key_metrics['duplication_rate'] = quality['fragment_inflation'].get('inflation_rate_percent', 0)

            if 'normalized_efficiency' in quality:
                key_metrics['storage_efficiency'] = quality['normalized_efficiency'].get('efficiency_score', 0)

        # Extract from network analysis
        if 'network' in analysis_results:
            network = analysis_results['network']
            if 'network_metrics' in network:
                metrics = network['network_metrics']
                key_metrics['graph_density'] = metrics.get('density', 0)

            if 'connectivity' in network:
                conn = network['connectivity']
                key_metrics['isolated_components'] = conn.get('isolated_pages', 0)
                key_metrics['largest_component_percent'] = conn.get('largest_component_percentage', 0)

        # Extract from pathway analysis
        if 'pathway' in analysis_results:
            pathway = analysis_results['pathway']
            if 'architecture' in pathway:
                arch = pathway['architecture']
                key_metrics['depth_efficiency'] = 100 - min(arch.get('max_depth', 0) * 10, 100)

        return key_metrics

    def load_snapshot(self, snapshot_id: str) -> Optional[Dict]:
        """Load a specific snapshot by ID."""
        filepath = self.snapshots_dir / f"{snapshot_id}.json"

        if not filepath.exists():
            print(f" Snapshot not found: {snapshot_id}")
            return None

        with open(filepath, 'r') as f:
            return json.load(f)

    def list_snapshots(self) -> List[Dict]:
        """List all available snapshots."""
        snapshots = []

        for filepath in sorted(self.snapshots_dir.glob("*.json")):
            try:
                with open(filepath, 'r') as f:
                    snapshot = json.load(f)
                    snapshots.append({
                        "snapshot_id": snapshot['snapshot_id'],
                        "timestamp": snapshot['timestamp'],
                        "metadata": snapshot.get('metadata', {})
                    })
            except Exception as e:
                print(f"Warning: Could not load {filepath.name}: {e}")

        return snapshots

    def compare_snapshots(self, snapshot1_id: str, snapshot2_id: str) -> Dict:
        """
        Compare two snapshots and calculate differences.

        Args:
            snapshot1_id: ID of first snapshot (baseline)
            snapshot2_id: ID of second snapshot (comparison)

        Returns:
            Dictionary with comparison results
        """
        snap1 = self.load_snapshot(snapshot1_id)
        snap2 = self.load_snapshot(snapshot2_id)

        if not snap1 or not snap2:
            return {}

        comparison = {
            "baseline": {
                "snapshot_id": snapshot1_id,
                "timestamp": snap1['timestamp']
            },
            "comparison": {
                "snapshot_id": snapshot2_id,
                "timestamp": snap2['timestamp']
            },
            "metrics_delta": {},
            "improvements": [],
            "regressions": []
        }

        # Calculate deltas
        metrics1 = snap1['metrics']
        metrics2 = snap2['metrics']

        for key in metrics1.keys():
            if key in metrics2:
                val1 = metrics1[key]
                val2 = metrics2[key]

                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    delta = val2 - val1
                    percent_change = (delta / val1 * 100) if val1 != 0 else 0

                    comparison['metrics_delta'][key] = {
                        "baseline": val1,
                        "current": val2,
                        "delta": delta,
                        "percent_change": percent_change
                    }

                    # Identify improvements/regressions
                    if self._is_improvement(key, delta):
                        comparison['improvements'].append({
                            "metric": key,
                            "delta": delta,
                            "percent": percent_change
                        })
                    elif self._is_regression(key, delta):
                        comparison['regressions'].append({
                            "metric": key,
                            "delta": delta,
                            "percent": percent_change
                        })

        return comparison

    def _is_improvement(self, metric_name: str, delta: float) -> bool:
        """Determine if a delta represents an improvement."""
        # Metrics where increase is good
        positive_metrics = {
            'data_quality_score', 'extraction_success_rate', 'storage_efficiency',
            'depth_efficiency', 'largest_component_percent', 'pages_with_title',
            'pages_with_links', 'urls_per_second'
        }

        # Metrics where decrease is good
        negative_metrics = {
            'error_rate', 'duplication_rate', 'isolated_components',
            'avg_response_time_ms'
        }

        if metric_name in positive_metrics:
            return delta > 1  # Improvement if increased
        elif metric_name in negative_metrics:
            return delta < -1  # Improvement if decreased

        return False

    def _is_regression(self, metric_name: str, delta: float) -> bool:
        """Determine if a delta represents a regression."""
        # Opposite of improvement
        positive_metrics = {
            'data_quality_score', 'extraction_success_rate', 'storage_efficiency',
            'depth_efficiency', 'largest_component_percent', 'pages_with_title',
            'pages_with_links', 'urls_per_second'
        }

        negative_metrics = {
            'error_rate', 'duplication_rate', 'isolated_components',
            'avg_response_time_ms'
        }

        if metric_name in positive_metrics:
            return delta < -1  # Regression if decreased
        elif metric_name in negative_metrics:
            return delta > 1  # Regression if increased

        return False

    def generate_trend_report(self, metric_name: str, limit: int = 10) -> Dict:
        """
        Generate a trend report for a specific metric over time.

        Args:
            metric_name: Name of metric to track
            limit: Maximum number of snapshots to include

        Returns:
            Trend data
        """
        snapshots = self.list_snapshots()[-limit:]  # Get most recent

        trend_data = {
            "metric": metric_name,
            "data_points": [],
            "trend": "unknown"
        }

        for snapshot_info in snapshots:
            snapshot = self.load_snapshot(snapshot_info['snapshot_id'])
            if snapshot and metric_name in snapshot['metrics']:
                trend_data['data_points'].append({
                    "timestamp": snapshot['timestamp'],
                    "value": snapshot['metrics'][metric_name]
                })

        # Determine trend direction
        if len(trend_data['data_points']) >= 2:
            first_val = trend_data['data_points'][0]['value']
            last_val = trend_data['data_points'][-1]['value']

            if isinstance(first_val, (int, float)) and isinstance(last_val, (int, float)):
                if last_val > first_val * 1.05:
                    trend_data['trend'] = "improving" if self._is_improvement(metric_name, last_val - first_val) else "worsening"
                elif last_val < first_val * 0.95:
                    trend_data['trend'] = "worsening" if self._is_improvement(metric_name, last_val - first_val) else "improving"
                else:
                    trend_data['trend'] = "stable"

        return trend_data

    def generate_summary_report(self) -> Dict:
        """Generate a summary report of all tracked metrics."""
        snapshots = self.list_snapshots()

        if len(snapshots) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 snapshots to generate trends"
            }

        # Compare latest with previous
        latest = snapshots[-1]
        previous = snapshots[-2]

        comparison = self.compare_snapshots(previous['snapshot_id'], latest['snapshot_id'])

        # Key metrics to track
        key_metrics = [
            'data_quality_score',
            'duplication_rate',
            'urls_per_second',
            'error_rate',
            'storage_efficiency'
        ]

        trends = {}
        for metric in key_metrics:
            trends[metric] = self.generate_trend_report(metric, limit=5)

        return {
            "status": "success",
            "total_snapshots": len(snapshots),
            "latest_snapshot": latest,
            "comparison_with_previous": comparison,
            "trends": trends,
            "summary": self._generate_text_summary(comparison, trends)
        }

    def _generate_text_summary(self, comparison: Dict, trends: Dict) -> str:
        """Generate human-readable summary."""
        improvements = comparison.get('improvements', [])
        regressions = comparison.get('regressions', [])

        summary = []
        summary.append(f"Performance Comparison:")
        summary.append(f"  Improvements: {len(improvements)}")
        summary.append(f"  Regressions: {len(regressions)}")

        if improvements:
            summary.append("\nTop Improvements:")
            for imp in improvements[:3]:
                summary.append(f"  - {imp['metric']}: {imp['percent']:+.1f}%")

        if regressions:
            summary.append("\nTop Regressions:")
            for reg in regressions[:3]:
                summary.append(f"  - {reg['metric']}: {reg['percent']:+.1f}%")

        return "\n".join(summary)


def create_tracker(history_dir: str = "metrics_history") -> MetricsTracker:
    """Create a metrics tracker instance."""
    return MetricsTracker(history_dir)
