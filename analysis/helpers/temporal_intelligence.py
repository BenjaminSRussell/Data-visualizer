"""
Temporal Pattern Intelligence

Purpose: Expose crawl velocity patterns and content lifecycle indicators.
Current temporal analysis (statistical_analyzer.py:380-410) only examines discovery
timestamps. These helpers detect sophisticated patterns like crawl waves, content
freshness zones, and parent-child discovery lag.

Integration Points:
- Enhances temporal_patterns in statistical_analyzer.py (lines 374-400)
- Provides crawl behavior insights beyond simple timestamp bucketing
"""

from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import numpy as np


def detect_crawl_waves(data: List[Dict], wave_threshold_seconds: int = 300) -> Dict:
    """
    Detect crawl wave patterns (burst detection, cyclical patterns).

    Line 395's simple bucketing misses sophisticated patterns like "this subdomain
    gets updated every Tuesday" or "these pages follow a waterfall discovery pattern".

    Args:
        data: List of URL dictionaries with discovered_at timestamps
        wave_threshold_seconds: Time window to group discovery events (default 5 min)

    Returns:
        Dictionary with wave patterns and characteristics

    Example:
        {
            'waves': [
                {
                    'wave_id': 1,
                    'start_time': 1234567890,
                    'end_time': 1234568190,
                    'duration_seconds': 300,
                    'url_count': 150,
                    'velocity': 0.5,  # URLs per second
                    'pattern_type': 'burst'
                }
            ],
            'total_waves': 5,
            'dominant_pattern': 'burst',
            'cyclical_indicators': {...}
        }
    """
    # Extract timestamps
    timestamp_data = []
    for item in data:
        discovered_at = item.get('discovered_at')
        if discovered_at:
            timestamp_data.append({
                'timestamp': discovered_at,
                'url': item.get('url', ''),
                'depth': item.get('depth', 0),
                'parent_url': item.get('parent_url')
            })

    if not timestamp_data:
        return {
            'waves': [],
            'total_waves': 0,
            'dominant_pattern': None,
            'available': False
        }

    # Sort by timestamp
    timestamp_data.sort(key=lambda x: x['timestamp'])

    # Detect waves using time gaps
    waves = []
    current_wave = {
        'wave_id': 1,
        'urls': [],
        'start_time': timestamp_data[0]['timestamp'],
        'end_time': timestamp_data[0]['timestamp']
    }

    for i, entry in enumerate(timestamp_data):
        timestamp = entry['timestamp']

        # Check if this entry belongs to current wave
        time_gap = timestamp - current_wave['end_time']

        if time_gap <= wave_threshold_seconds:
            # Continue current wave
            current_wave['urls'].append(entry)
            current_wave['end_time'] = timestamp
        else:
            # Finalize current wave
            if len(current_wave['urls']) > 0:
                waves.append(_finalize_wave(current_wave))

            # Start new wave
            current_wave = {
                'wave_id': len(waves) + 1,
                'urls': [entry],
                'start_time': timestamp,
                'end_time': timestamp
            }

    # Don't forget the last wave
    if len(current_wave['urls']) > 0:
        waves.append(_finalize_wave(current_wave))

    # Analyze patterns
    pattern_types = Counter([w['pattern_type'] for w in waves])
    dominant_pattern = pattern_types.most_common(1)[0][0] if pattern_types else None

    # Check for cyclical patterns
    cyclical_indicators = _detect_cyclical_patterns(waves)

    return {
        'waves': waves,
        'total_waves': len(waves),
        'dominant_pattern': dominant_pattern,
        'pattern_distribution': dict(pattern_types),
        'cyclical_indicators': cyclical_indicators,
        'available': True,
        'total_urls_analyzed': len(timestamp_data)
    }


def identify_content_freshness_zones(data: List[Dict], staleness_threshold_days: int = 30) -> Dict:
    """
    Identify content freshness zones (active vs archived sections).

    Distinguishes between actively maintained sections and archived/stale content.

    Args:
        data: List of URL dictionaries with discovered_at timestamps
        staleness_threshold_days: Days after which content is considered stale

    Returns:
        Dictionary with freshness zones and recommendations

    Example:
        {
            'zones': {
                '/blog/': {'freshness': 'active', 'avg_age_days': 5, 'url_count': 50},
                '/archive/': {'freshness': 'stale', 'avg_age_days': 180, 'url_count': 100}
            },
            'active_percentage': 33.3,
            'stale_percentage': 66.7
        }
    """
    if not data:
        return {
            'zones': {},
            'available': False
        }

    # Get reference timestamp (most recent)
    all_timestamps = [item.get('discovered_at') for item in data if item.get('discovered_at')]
    if not all_timestamps:
        return {
            'zones': {},
            'available': False
        }

    reference_time = max(all_timestamps)
    staleness_threshold_seconds = staleness_threshold_days * 24 * 3600

    # Group by path prefix
    path_groups = defaultdict(list)

    for item in data:
        url = item.get('url', '')
        discovered_at = item.get('discovered_at')

        if not url or not discovered_at:
            continue

        # Extract path prefix (first segment)
        from urllib.parse import urlparse
        parsed = urlparse(url)
        segments = [s for s in parsed.path.split('/') if s]
        prefix = '/' + segments[0] + '/' if segments else '/'

        age_seconds = reference_time - discovered_at

        path_groups[prefix].append({
            'url': url,
            'age_seconds': age_seconds,
            'age_days': age_seconds / (24 * 3600)
        })

    # Analyze each zone
    zones = {}
    total_urls = len(data)

    for prefix, urls in path_groups.items():
        avg_age_seconds = np.mean([u['age_seconds'] for u in urls])
        avg_age_days = avg_age_seconds / (24 * 3600)

        # Classify freshness
        if avg_age_seconds < staleness_threshold_seconds:
            freshness = 'active'
        elif avg_age_seconds < staleness_threshold_seconds * 2:
            freshness = 'aging'
        else:
            freshness = 'stale'

        zones[prefix] = {
            'freshness': freshness,
            'avg_age_days': avg_age_days,
            'url_count': len(urls),
            'percentage': (len(urls) / total_urls) * 100,
            'oldest_age_days': max(u['age_days'] for u in urls),
            'newest_age_days': min(u['age_days'] for u in urls)
        }

    # Calculate overall metrics
    active_count = sum(1 for z in zones.values() if z['freshness'] == 'active')
    aging_count = sum(1 for z in zones.values() if z['freshness'] == 'aging')
    stale_count = sum(1 for z in zones.values() if z['freshness'] == 'stale')

    total_zones = len(zones)

    return {
        'zones': zones,
        'total_zones': total_zones,
        'active_zones': active_count,
        'aging_zones': aging_count,
        'stale_zones': stale_count,
        'active_percentage': (active_count / total_zones * 100) if total_zones > 0 else 0,
        'stale_percentage': (stale_count / total_zones * 100) if total_zones > 0 else 0,
        'available': True
    }


def calculate_discovery_efficiency(data: List[Dict]) -> Dict:
    """
    Calculate time-to-discovery efficiency metrics.

    Measures how efficiently the crawler discovers content across different
    sections of the site.

    Args:
        data: List of URL dictionaries with discovered_at and depth

    Returns:
        Dictionary with discovery efficiency metrics

    Example:
        {
            'avg_discovery_time_per_depth': {0: 0, 1: 5, 2: 15, 3: 45},
            'efficiency_score': 78.5,
            'bottleneck_depths': [3, 4]
        }
    """
    if not data:
        return {
            'available': False
        }

    # Get timestamps
    all_timestamps = [item.get('discovered_at') for item in data if item.get('discovered_at')]
    if not all_timestamps:
        return {
            'available': False
        }

    start_time = min(all_timestamps)

    # Group by depth
    depth_discovery_times = defaultdict(list)

    for item in data:
        discovered_at = item.get('discovered_at')
        depth = item.get('depth', 0)

        if discovered_at:
            time_from_start = discovered_at - start_time
            depth_discovery_times[depth].append(time_from_start)

    # Calculate metrics per depth
    avg_discovery_per_depth = {}
    depth_efficiency_scores = {}

    for depth, times in depth_discovery_times.items():
        avg_time = np.mean(times)
        avg_discovery_per_depth[depth] = avg_time

        # Efficiency score: lower time relative to depth is better
        # Expected time grows linearly with depth
        expected_time = depth * 10  # 10 seconds per depth level (baseline)
        if expected_time == 0:
            efficiency = 100.0
        else:
            efficiency = max(0, min(100, (expected_time / avg_time) * 100))

        depth_efficiency_scores[depth] = efficiency

    # Overall efficiency score
    overall_efficiency = np.mean(list(depth_efficiency_scores.values())) if depth_efficiency_scores else 0

    # Identify bottleneck depths (low efficiency)
    bottleneck_threshold = 50
    bottleneck_depths = [
        depth for depth, score in depth_efficiency_scores.items()
        if score < bottleneck_threshold
    ]

    return {
        'avg_discovery_time_per_depth': {d: round(t, 2) for d, t in avg_discovery_per_depth.items()},
        'depth_efficiency_scores': {d: round(s, 2) for d, s in depth_efficiency_scores.items()},
        'overall_efficiency_score': round(overall_efficiency, 2),
        'bottleneck_depths': sorted(bottleneck_depths),
        'fastest_depth': min(depth_efficiency_scores.items(), key=lambda x: x[1])[0] if depth_efficiency_scores else None,
        'slowest_depth': max(depth_efficiency_scores.items(), key=lambda x: x[1])[0] if depth_efficiency_scores else None,
        'available': True
    }


def map_discovery_lag_patterns(data: List[Dict]) -> Dict:
    """
    Map parent-child discovery lag patterns.

    Identifies delays between discovering a parent page and its child pages,
    which can indicate poor internal linking or crawler inefficiency.

    Args:
        data: List of URL dictionaries with parent_url and discovered_at

    Returns:
        Dictionary with discovery lag analysis

    Example:
        {
            'avg_lag_seconds': 120,
            'lag_distribution': {0-60: 50, 60-300: 30, 300+: 20},
            'problem_parents': [
                {'url': '...', 'avg_child_lag': 600, 'child_count': 10}
            ]
        }
    """
    if not data:
        return {
            'available': False
        }

    # Build parent-child discovery map
    url_discovery_time = {}
    parent_child_map = defaultdict(list)

    for item in data:
        url = item.get('url', '')
        discovered_at = item.get('discovered_at')
        parent_url = item.get('parent_url')

        if url and discovered_at:
            url_discovery_time[url] = discovered_at

        if parent_url and parent_url != url:
            parent_child_map[parent_url].append(url)

    # Calculate lags
    lags = []
    parent_lag_stats = {}

    for parent_url, child_urls in parent_child_map.items():
        parent_time = url_discovery_time.get(parent_url)

        if not parent_time:
            continue

        child_lags = []

        for child_url in child_urls:
            child_time = url_discovery_time.get(child_url)

            if child_time:
                lag = child_time - parent_time
                if lag >= 0:  # Only count forward lags
                    lags.append(lag)
                    child_lags.append(lag)

        if child_lags:
            parent_lag_stats[parent_url] = {
                'avg_child_lag': np.mean(child_lags),
                'max_child_lag': max(child_lags),
                'child_count': len(child_lags)
            }

    if not lags:
        return {
            'available': False
        }

    # Calculate distribution
    lag_distribution = {
        '0-60s': sum(1 for l in lags if l <= 60),
        '60-300s': sum(1 for l in lags if 60 < l <= 300),
        '300-600s': sum(1 for l in lags if 300 < l <= 600),
        '600+s': sum(1 for l in lags if l > 600)
    }

    # Identify problem parents (high lag)
    problem_threshold = np.percentile(lags, 75) if lags else 0
    problem_parents = [
        {
            'url': url,
            'avg_child_lag': round(stats['avg_child_lag'], 2),
            'max_child_lag': round(stats['max_child_lag'], 2),
            'child_count': stats['child_count']
        }
        for url, stats in parent_lag_stats.items()
        if stats['avg_child_lag'] > problem_threshold
    ]

    # Sort by lag
    problem_parents.sort(key=lambda x: x['avg_child_lag'], reverse=True)

    return {
        'avg_lag_seconds': round(np.mean(lags), 2),
        'median_lag_seconds': round(np.median(lags), 2),
        'max_lag_seconds': round(max(lags), 2),
        'min_lag_seconds': round(min(lags), 2),
        'lag_distribution': lag_distribution,
        'total_parent_child_pairs': len(lags),
        'problem_parents': problem_parents[:10],  # Top 10
        'problem_parent_count': len(problem_parents),
        'available': True
    }


# Helper functions

def _finalize_wave(wave_data: Dict) -> Dict:
    """Finalize wave with computed metrics."""
    urls = wave_data['urls']
    start_time = wave_data['start_time']
    end_time = wave_data['end_time']

    duration = end_time - start_time
    url_count = len(urls)

    # Calculate velocity (URLs per second)
    velocity = url_count / duration if duration > 0 else float('inf')

    # Classify pattern type
    if duration < 60 and url_count > 50:
        pattern_type = 'burst'
    elif duration > 3600 and url_count > 100:
        pattern_type = 'sustained'
    elif velocity > 1.0:
        pattern_type = 'rapid'
    else:
        pattern_type = 'steady'

    # Analyze depth distribution in wave
    depths = [u['depth'] for u in urls]
    avg_depth = np.mean(depths) if depths else 0

    return {
        'wave_id': wave_data['wave_id'],
        'start_time': start_time,
        'end_time': end_time,
        'duration_seconds': duration,
        'url_count': url_count,
        'velocity': round(velocity, 4),
        'pattern_type': pattern_type,
        'avg_depth': round(avg_depth, 2),
        'depth_range': [min(depths), max(depths)] if depths else [0, 0]
    }


def _detect_cyclical_patterns(waves: List[Dict]) -> Dict:
    """Detect if waves follow a cyclical pattern."""
    if len(waves) < 3:
        return {
            'detected': False,
            'reason': 'insufficient_waves'
        }

    # Calculate inter-wave intervals
    intervals = []
    for i in range(len(waves) - 1):
        interval = waves[i + 1]['start_time'] - waves[i]['end_time']
        intervals.append(interval)

    if not intervals:
        return {
            'detected': False
        }

    # Check for consistency in intervals
    avg_interval = np.mean(intervals)
    std_interval = np.std(intervals)
    coefficient_of_variation = std_interval / avg_interval if avg_interval > 0 else float('inf')

    # Cyclical if CV < 0.3 (intervals are consistent)
    is_cyclical = coefficient_of_variation < 0.3

    return {
        'detected': is_cyclical,
        'avg_interval_seconds': round(avg_interval, 2),
        'std_interval_seconds': round(std_interval, 2),
        'coefficient_of_variation': round(coefficient_of_variation, 4),
        'estimated_cycle_time': round(avg_interval, 2) if is_cyclical else None
    }
