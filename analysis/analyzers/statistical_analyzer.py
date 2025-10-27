"""
Statistical URL Analysis - Deep Metrics and Distributions

Purpose: Extract statistical insights from URL data including distributions,
         correlations, anomalies, and patterns
"""

import json
import numpy as np
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from scipy import stats
import re


class StatisticalAnalyzer:
    """Perform comprehensive statistical analysis on URL data."""

    def __init__(self):
        self.urls = []
        self.depths = []
        self.path_lengths = []
        self.query_counts = []
        self.fragment_counts = []
        self.link_counts = []

    def analyze(self, data: List[Dict]) -> Dict:
        """
        Perform comprehensive statistical analysis.

        Args:
            data: List of URL dictionaries from JSONL

        Returns:
            Statistical analysis results
        """
        self._extract_features(data)

        results = {
            'summary_stats': self._compute_summary_stats(),
            'distributions': self._analyze_distributions(),
            'correlations': self._compute_correlations(),
            'anomalies': self._detect_anomalies(),
            'depth_analysis': self._analyze_depth_patterns(),
            'link_analysis': self._analyze_link_patterns(),
            'url_health': self._compute_url_health(),
            'temporal_patterns': self._analyze_temporal_patterns(data),
            'content_analysis': self._analyze_content_patterns(data)
        }

        return results

    def _extract_features(self, data: List[Dict]):
        """Extract numerical features from URL data."""
        for item in data:
            url = item.get('url', '')
            self.urls.append(url)

            # depth
            depth = item.get('depth', 0)
            self.depths.append(depth)

            # parse url
            try:
                parsed = urlparse(url)

                # path length
                path_len = len(parsed.path)
                self.path_lengths.append(path_len)

                # query parameters
                query_count = len(parsed.query.split('&')) if parsed.query else 0
                self.query_counts.append(query_count)

                # fragment
                self.fragment_counts.append(1 if parsed.fragment else 0)

            except:
                self.path_lengths.append(0)
                self.query_counts.append(0)
                self.fragment_counts.append(0)

            # links
            links = item.get('links', [])
            self.link_counts.append(len(links))

    def _compute_summary_stats(self) -> Dict:
        """Compute summary statistics for all features."""

        def stats_dict(data, name):
            arr = np.array(data)
            return {
                f'{name}_count': len(arr),
                f'{name}_mean': float(np.mean(arr)) if len(arr) > 0 else 0,
                f'{name}_median': float(np.median(arr)) if len(arr) > 0 else 0,
                f'{name}_std': float(np.std(arr)) if len(arr) > 0 else 0,
                f'{name}_min': float(np.min(arr)) if len(arr) > 0 else 0,
                f'{name}_max': float(np.max(arr)) if len(arr) > 0 else 0,
                f'{name}_q25': float(np.percentile(arr, 25)) if len(arr) > 0 else 0,
                f'{name}_q75': float(np.percentile(arr, 75)) if len(arr) > 0 else 0,
            }

        summary = {
            'total_urls': len(self.urls),
        }

        summary.update(stats_dict(self.depths, 'depth'))
        summary.update(stats_dict(self.path_lengths, 'path_length'))
        summary.update(stats_dict(self.query_counts, 'query_params'))
        summary.update(stats_dict(self.link_counts, 'outbound_links'))

        return summary

    def _analyze_distributions(self) -> Dict:
        """Analyze distributions of key metrics."""

        distributions = {}

        # depth distribution
        depth_dist = Counter(self.depths)
        distributions['depth_distribution'] = dict(sorted(depth_dist.items()))
        distributions['depth_histogram'] = self._create_histogram(self.depths, 'Depth')

        # path length distribution
        distributions['path_length_histogram'] = self._create_histogram(
            self.path_lengths, 'Path Length', bins=20
        )

        # link count distribution
        distributions['link_count_histogram'] = self._create_histogram(
            self.link_counts, 'Link Count', bins=20
        )

        # test for normality
        if len(self.depths) > 8:
            _, p_value = stats.shapiro(self.depths[:5000])  # shapiro test max 5000 samples
            distributions['depth_normality_test'] = {
                'is_normal': p_value > 0.05,
                'p_value': float(p_value)
            }

        return distributions

    def _create_histogram(self, data, name, bins=10) -> Dict:
        """Create histogram data."""
        if not data:
            return {'bins': [], 'counts': []}

        counts, bin_edges = np.histogram(data, bins=bins)

        return {
            'bins': [float(x) for x in bin_edges],
            'counts': [int(x) for x in counts],
            'name': name
        }

    def _compute_correlations(self) -> Dict:
        """Compute correlations between features."""

        correlations = {}

        # depth vs link count
        if len(self.depths) > 1 and len(self.link_counts) > 1:
            corr, p_value = stats.pearsonr(self.depths, self.link_counts)
            correlations['depth_vs_link_count'] = {
                'correlation': float(corr),
                'p_value': float(p_value),
                'significant': p_value < 0.05,
                'interpretation': self._interpret_correlation(corr)
            }

        # depth vs path length
        if len(self.depths) > 1 and len(self.path_lengths) > 1:
            corr, p_value = stats.pearsonr(self.depths, self.path_lengths)
            correlations['depth_vs_path_length'] = {
                'correlation': float(corr),
                'p_value': float(p_value),
                'significant': p_value < 0.05,
                'interpretation': self._interpret_correlation(corr)
            }

        # path length vs link count
        if len(self.path_lengths) > 1 and len(self.link_counts) > 1:
            corr, p_value = stats.pearsonr(self.path_lengths, self.link_counts)
            correlations['path_length_vs_link_count'] = {
                'correlation': float(corr),
                'p_value': float(p_value),
                'significant': p_value < 0.05,
                'interpretation': self._interpret_correlation(corr)
            }

        return correlations

    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation coefficient."""
        abs_corr = abs(corr)
        direction = "positive" if corr > 0 else "negative"

        if abs_corr < 0.1:
            strength = "negligible"
        elif abs_corr < 0.3:
            strength = "weak"
        elif abs_corr < 0.5:
            strength = "moderate"
        elif abs_corr < 0.7:
            strength = "strong"
        else:
            strength = "very strong"

        return f"{strength} {direction} correlation"

    def _detect_anomalies(self) -> Dict:
        """Detect anomalies using statistical methods."""

        anomalies = {}

        # depth anomalies (using iqr method)
        anomalies['depth_outliers'] = self._find_outliers(
            self.depths, self.urls, 'depth'
        )

        # path length anomalies
        anomalies['path_length_outliers'] = self._find_outliers(
            self.path_lengths, self.urls, 'path_length'
        )

        # link count anomalies
        anomalies['link_count_outliers'] = self._find_outliers(
            self.link_counts, self.urls, 'link_count'
        )

        return anomalies

    def _find_outliers(self, data, urls, feature_name) -> Dict:
        """Find outliers using IQR method."""
        if len(data) == 0:
            return {'count': 0, 'examples': []}

        arr = np.array(data)
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outlier_indices = np.where((arr < lower_bound) | (arr > upper_bound))[0]

        examples = []
        for idx in outlier_indices[:10]:  # limit to 10 examples
            examples.append({
                'url': urls[idx],
                'value': float(data[idx]),
                'z_score': float((data[idx] - np.mean(arr)) / np.std(arr)) if np.std(arr) > 0 else 0
            })

        return {
            'count': len(outlier_indices),
            'percentage': (len(outlier_indices) / len(data)) * 100,
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
            'examples': examples
        }

    def _analyze_depth_patterns(self) -> Dict:
        """Analyze depth-specific patterns."""

        depth_patterns = defaultdict(lambda: {
            'count': 0,
            'avg_links': 0,
            'avg_path_length': 0,
            'has_fragment': 0,
            'has_query': 0
        })

        for i, depth in enumerate(self.depths):
            pattern = depth_patterns[depth]
            pattern['count'] += 1
            pattern['avg_links'] += self.link_counts[i]
            pattern['avg_path_length'] += self.path_lengths[i]
            pattern['has_fragment'] += self.fragment_counts[i]
            pattern['has_query'] += 1 if self.query_counts[i] > 0 else 0

        # calculate averages
        for depth, pattern in depth_patterns.items():
            count = pattern['count']
            pattern['avg_links'] = pattern['avg_links'] / count
            pattern['avg_path_length'] = pattern['avg_path_length'] / count
            pattern['fragment_percentage'] = (pattern['has_fragment'] / count) * 100
            pattern['query_percentage'] = (pattern['has_query'] / count) * 100

        return dict(depth_patterns)

    def _analyze_link_patterns(self) -> Dict:
        """Analyze link patterns."""

        link_analysis = {}

        # pages with no links
        no_links = sum(1 for count in self.link_counts if count == 0)
        link_analysis['dead_end_pages'] = {
            'count': no_links,
            'percentage': (no_links / len(self.link_counts)) * 100 if self.link_counts else 0
        }

        # hub pages (top 5% by link count)
        if self.link_counts:
            threshold = np.percentile(self.link_counts, 95)
            hub_indices = [i for i, count in enumerate(self.link_counts) if count >= threshold]

            link_analysis['hub_pages'] = {
                'count': len(hub_indices),
                'threshold': float(threshold),
                'examples': [
                    {'url': self.urls[i], 'link_count': self.link_counts[i]}
                    for i in hub_indices[:10]
                ]
            }

        return link_analysis

    def _compute_url_health(self) -> Dict:
        """Compute overall URL health metrics."""

        health = {}

        # url length health (optimal: 50-100 chars)
        optimal_length = 0
        for url in self.urls:
            if 50 <= len(url) <= 100:
                optimal_length += 1

        health['url_length_score'] = (optimal_length / len(self.urls)) * 100 if self.urls else 0

        # depth health (optimal: 2-4 levels)
        optimal_depth = sum(1 for d in self.depths if 2 <= d <= 4)
        health['depth_score'] = (optimal_depth / len(self.depths)) * 100 if self.depths else 0

        # fragment health (fragments can cause duplicate content)
        fragment_rate = (sum(self.fragment_counts) / len(self.fragment_counts)) * 100 if self.fragment_counts else 0
        health['fragment_score'] = max(0, 100 - fragment_rate)

        # overall health score
        health['overall_health'] = (
            health['url_length_score'] * 0.3 +
            health['depth_score'] * 0.4 +
            health['fragment_score'] * 0.3
        )

        health['health_grade'] = self._get_health_grade(health['overall_health'])

        return health

    def _get_health_grade(self, score: float) -> str:
        """Convert health score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _analyze_temporal_patterns(self, data: List[Dict]) -> Dict:
        """Analyze temporal patterns from discovered_at timestamps."""

        timestamps = [item.get('discovered_at') for item in data if item.get('discovered_at')]

        if not timestamps:
            return {'available': False}

        temporal = {
            'available': True,
            'first_discovered': min(timestamps),
            'last_discovered': max(timestamps),
            'time_span_seconds': max(timestamps) - min(timestamps),
            'discovery_rate': len(timestamps) / (max(timestamps) - min(timestamps)) if max(timestamps) != min(timestamps) else 0
        }

        # discovery timeline (buckets)
        time_range = max(timestamps) - min(timestamps)
        if time_range > 0:
            bucket_size = time_range / 10
            buckets = Counter()
            for ts in timestamps:
                bucket = int((ts - min(timestamps)) / bucket_size)
                buckets[bucket] += 1
            temporal['discovery_timeline'] = dict(buckets)

        return temporal

    def _analyze_content_patterns(self, data: List[Dict]) -> Dict:
        """Analyze content type and status code patterns."""

        content = {}

        # content types
        content_types = Counter()
        for item in data:
            ct = item.get('content_type')
            if ct:
                # simplify content type
                simplified = ct.split(';')[0].strip()
                content_types[simplified] += 1

        content['content_types'] = dict(content_types.most_common(10))

        # status codes
        status_codes = Counter()
        for item in data:
            sc = item.get('status_code')
            if sc:
                status_codes[sc] += 1

        content['status_codes'] = dict(status_codes)

        # success rate
        successful = sum(count for code, count in status_codes.items() if code == 200)
        total_with_status = sum(status_codes.values())
        content['success_rate'] = (successful / total_with_status * 100) if total_with_status > 0 else 0

        return content


def execute(data: List[Dict]) -> Dict:
    """
    Main execution function for statistical analysis.

    Args:
        data: List of URL dictionaries from JSONL

    Returns:
        Statistical analysis results
    """
    analyzer = StatisticalAnalyzer()
    return analyzer.analyze(data)


def print_summary(results: Dict):
    """Print human-readable summary of statistical analysis."""

    print("\n" + "="*80)
    print("STATISTICAL ANALYSIS SUMMARY")
    print("="*80)

    # summary stats
    summary = results['summary_stats']
    print(f"\nDataset Overview:")
    print(f"  Total URLs: {summary['total_urls']:,}")
    print(f"  Depth Range: {summary['depth_min']:.0f} - {summary['depth_max']:.0f} (avg: {summary['depth_mean']:.2f})")
    print(f"  Path Length Range: {summary['path_length_min']:.0f} - {summary['path_length_max']:.0f} (avg: {summary['path_length_mean']:.2f})")
    print(f"  Avg Links per Page: {summary['outbound_links_mean']:.2f}")

    # health
    health = results['url_health']
    print(f"\nURL Health Score: {health['overall_health']:.1f}/100 (Grade: {health['health_grade']})")
    print(f"  Length Optimization: {health['url_length_score']:.1f}%")
    print(f"  Depth Optimization: {health['depth_score']:.1f}%")
    print(f"  Fragment Health: {health['fragment_score']:.1f}%")

    # correlations
    if results['correlations']:
        print(f"\nKey Correlations:")
        for name, corr in results['correlations'].items():
            if corr.get('significant'):
                print(f"  {name}: {corr['interpretation']} (r={corr['correlation']:.3f})")

    # anomalies
    print(f"\nAnomalies Detected:")
    for name, anomaly in results['anomalies'].items():
        if anomaly['count'] > 0:
            print(f"  {name}: {anomaly['count']} outliers ({anomaly['percentage']:.1f}%)")

    print("\n" + "="*80)