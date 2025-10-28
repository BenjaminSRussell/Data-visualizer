"""
Data Quality Analyzer - Detect Data Inflation and Duplication

Purpose: Identify redundant data, duplicate URLs, and storage waste.
         Critical for understanding true vs inflated dataset size.
"""

from collections import Counter, defaultdict
from typing import Dict, List

from analysis.shared.url_components import get_components, get_normalized_url


class DataQualityAnalyzer:
    """Analyze data quality, duplication, and inflation."""

    def __init__(self):
        self.urls = []
        self.normalized_urls = {}
        self.duplication_sources = defaultdict(list)

    def analyze(self, data: List[Dict]) -> Dict:
        """
        Perform comprehensive data quality analysis.

        Args:
            data: List of URL dictionaries from JSONL

        Returns:
            Data quality analysis results
        """
        self.urls = [item.get('url', '') for item in data if item.get('url')]

        results = {
            'summary': self._compute_summary(),
            'fragment_inflation': self._analyze_fragment_duplication(),
            'parameter_variations': self._analyze_parameter_duplication(),
            'timestamp_duplicates': self._analyze_timestamp_duplicates(data),
            'normalized_efficiency': self._analyze_normalization_impact(),
            'storage_waste': self._estimate_storage_waste(data),
            'tracking_param_pollution': self._analyze_tracking_params(),
            'overall_quality_score': 0  # Will be calculated at end
        }

        # Calculate overall quality score
        results['overall_quality_score'] = self._calculate_quality_score(results)

        return results

    def _compute_summary(self) -> Dict:
        """Compute summary statistics."""
        return {
            'total_urls': len(self.urls),
            'unique_urls': len(set(self.urls))
        }

    def _analyze_fragment_duplication(self) -> Dict:
        """Analyze URLs that differ only by fragment."""

        # Group URLs by base (without fragment)
        base_url_groups = defaultdict(list)

        for url in self.urls:
            normalized_no_frag = get_normalized_url(url, remove_fragment=True, remove_tracking=False)
            base_url_groups[normalized_no_frag].append(url)

        # Find groups with multiple URLs (duplicates)
        duplicates = {
            base: urls for base, urls in base_url_groups.items()
            if len(urls) > 1
        }

        # Count wasted URLs
        wasted_count = sum(len(urls) - 1 for urls in duplicates.values())
        inflation_rate = (wasted_count / len(self.urls) * 100) if self.urls else 0

        # Find worst offenders
        worst_offenders = sorted(
            duplicates.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]

        return {
            'duplicate_groups': len(duplicates),
            'wasted_urls': wasted_count,
            'inflation_rate_percent': inflation_rate,
            'unique_after_defrag': len(base_url_groups),
            'worst_offenders': [
                {
                    'base_url': base,
                    'duplicate_count': len(urls),
                    'examples': urls[:5]
                }
                for base, urls in worst_offenders
            ]
        }

    def _analyze_parameter_duplication(self) -> Dict:
        """Analyze URLs that differ only by query parameters."""

        # Group URLs by path only (no query params)
        path_groups = defaultdict(list)

        for url in self.urls:
            components = get_components(url)
            key = f"{components['scheme']}://{components['netloc']}{components['path_normalized']}"
            path_groups[key].append(url)

        # Find paths with multiple parameter variations
        variations = {
            path: urls for path, urls in path_groups.items()
            if len(urls) > 1
        }

        wasted_count = sum(len(urls) - 1 for urls in variations.values())
        inflation_rate = (wasted_count / len(self.urls) * 100) if self.urls else 0

        # Analyze tracking parameter variations
        tracking_waste = self._count_tracking_param_variations(variations)

        return {
            'paths_with_variations': len(variations),
            'wasted_urls': wasted_count,
            'inflation_rate_percent': inflation_rate,
            'tracking_param_waste': tracking_waste,
            'unique_after_deparam': len(path_groups)
        }

    def _count_tracking_param_variations(self, variations: Dict) -> Dict:
        """Count how many variations are due to tracking parameters only."""

        tracking_only_waste = 0

        for path, urls in variations.items():
            # Get normalized versions (removes tracking params)
            normalized = defaultdict(list)
            for url in urls:
                norm = get_normalized_url(url, remove_fragment=True, remove_tracking=True)
                normalized[norm].append(url)

            # Count groups where tracking params are the only difference
            for norm_url, original_urls in normalized.items():
                if len(original_urls) > 1:
                    tracking_only_waste += len(original_urls) - 1

        return {
            'tracking_only_duplicates': tracking_only_waste,
            'percent_of_total': (tracking_only_waste / len(self.urls) * 100) if self.urls else 0
        }

    def _analyze_timestamp_duplicates(self, data: List[Dict]) -> Dict:
        """Analyze same URL crawled multiple times."""

        # Group by URL
        url_timestamps = defaultdict(list)

        for item in data:
            url = item.get('url', '')
            timestamp = item.get('discovered_at')
            if url and timestamp:
                url_timestamps[url].append(timestamp)

        # Find URLs with multiple timestamps
        multi_crawl = {
            url: timestamps for url, timestamps in url_timestamps.items()
            if len(timestamps) > 1
        }

        total_recrawls = sum(len(timestamps) - 1 for timestamps in multi_crawl.values())

        return {
            'urls_crawled_multiple_times': len(multi_crawl),
            'total_recrawls': total_recrawls,
            'recrawl_waste_percent': (total_recrawls / len(self.urls) * 100) if self.urls else 0,
            'worst_recrawlers': sorted(
                multi_crawl.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]
        }

    def _analyze_normalization_impact(self) -> Dict:
        """Analyze impact of URL normalization."""

        # Count unique URLs after full normalization
        fully_normalized = set()
        for url in self.urls:
            normalized = get_normalized_url(url, remove_fragment=True, remove_tracking=True)
            fully_normalized.add(normalized)

        before = len(self.urls)
        after = len(fully_normalized)
        reduction = before - after
        reduction_percent = (reduction / before * 100) if before > 0 else 0

        return {
            'before_normalization': before,
            'after_normalization': after,
            'urls_reduced': reduction,
            'reduction_percent': reduction_percent,
            'efficiency_score': (after / before * 100) if before > 0 else 0
        }

    def _estimate_storage_waste(self, data: List[Dict]) -> Dict:
        """Estimate storage space wasted on duplicate data."""

        # Estimate average URL size in bytes
        total_size = sum(len(str(item)) for item in data)  # Rough estimate
        avg_size_per_url = total_size / len(data) if data else 0

        # Calculate waste from different sources
        fragment_waste = self._analyze_fragment_duplication()['wasted_urls']
        param_waste = self._analyze_parameter_duplication()['wasted_urls']
        recrawl_waste = self._analyze_timestamp_duplicates(data)['total_recrawls']

        total_wasted_urls = fragment_waste + param_waste + recrawl_waste
        wasted_mb = (total_wasted_urls * avg_size_per_url) / (1024 * 1024)

        return {
            'avg_bytes_per_url': int(avg_size_per_url),
            'wasted_urls': total_wasted_urls,
            'wasted_mb': wasted_mb,
            'wasted_percent': (total_wasted_urls / len(self.urls) * 100) if self.urls else 0
        }

    def _analyze_tracking_params(self) -> Dict:
        """Analyze tracking parameter pollution."""

        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', '_ga', '_gl', 'mc_cid', 'mc_eid',
            'ref', 'source', 'campaign'
        ]

        urls_with_tracking = 0
        tracking_param_counts = Counter()

        for url in self.urls:
            components = get_components(url)
            if components['has_query']:
                params = components['query_params']
                has_tracking = False
                for param in tracking_params:
                    if param in params:
                        tracking_param_counts[param] += 1
                        has_tracking = True

                if has_tracking:
                    urls_with_tracking += 1

        return {
            'urls_with_tracking_params': urls_with_tracking,
            'tracking_pollution_percent': (urls_with_tracking / len(self.urls) * 100) if self.urls else 0,
            'tracking_param_distribution': dict(tracking_param_counts.most_common(10))
        }

    def _calculate_quality_score(self, results: Dict) -> float:
        """Calculate overall data quality score (0-100)."""

        # Start with perfect score
        score = 100.0

        # Penalize fragment inflation
        frag_inflation = results['fragment_inflation']['inflation_rate_percent']
        score -= min(frag_inflation, 30)  # Max 30 point penalty

        # Penalize parameter variations
        param_inflation = results['parameter_variations']['inflation_rate_percent']
        score -= min(param_inflation * 0.5, 20)  # Max 20 point penalty

        # Penalize recrawls
        recrawl_waste = results['timestamp_duplicates']['recrawl_waste_percent']
        score -= min(recrawl_waste * 0.5, 15)  # Max 15 point penalty

        # Penalize tracking pollution
        tracking_pollution = results['tracking_param_pollution']['tracking_pollution_percent']
        score -= min(tracking_pollution * 0.2, 10)  # Max 10 point penalty

        return max(0, score)  # Ensure non-negative


def execute(data: List[Dict]) -> Dict:
    """
    Main execution function for data quality analysis.

    Args:
        data: List of URL dictionaries from JSONL

    Returns:
        Data quality analysis results
    """
    analyzer = DataQualityAnalyzer()
    return analyzer.analyze(data)


def print_summary(results: Dict):
    """Print human-readable summary of data quality analysis."""

    print("Data quality analysis summary")

    # Summary
    summary = results['summary']
    print("Dataset overview:")
    print(f"Total URLs: {summary['total_urls']:,}")
    print(f"Unique URLs: {summary['unique_urls']:,}")

    # Fragment inflation
    frag = results['fragment_inflation']
    print("Fragment inflation:")
    print(f"Wasted URLs: {frag['wasted_urls']:,} ({frag['inflation_rate_percent']:.1f}%)")
    print(f"Unique after defragmentation: {frag['unique_after_defrag']:,}")

    # Parameter variations
    param = results['parameter_variations']
    print("Parameter variations:")
    print(f"Wasted URLs: {param['wasted_urls']:,} ({param['inflation_rate_percent']:.1f}%)")
    print(f"Tracking param only: {param['tracking_param_waste']['tracking_only_duplicates']:,}")

    # Storage waste
    storage = results['storage_waste']
    print("Storage waste:")
    print(f"Wasted URLs: {storage['wasted_urls']:,}")
    print(f"Estimated waste: {storage['wasted_mb']:.2f} MB")

    # Overall quality
    score = results['overall_quality_score']
    grade = 'A' if score >= 90 else 'B' if score >= 80 else 'C' if score >= 70 else 'D' if score >= 60 else 'F'
    print(f"Overall quality score: {score:.1f}/100 (Grade: {grade})")
