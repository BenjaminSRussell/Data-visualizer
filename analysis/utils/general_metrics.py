"""
General Metrics - Centralized Depth and Statistical Metrics

Purpose: Single source of truth for depth distribution, depth patterns,
         and related statistical metrics. Eliminates redundant depth
         calculations across multiple analyzer modules.
"""

from typing import Dict, List
from collections import Counter, defaultdict
from analysis.utils.url_utilities import get_path_depth, parse_url_components


def calculate_depth_distribution(urls: List[str]) -> Dict:
    """
    Calculate comprehensive depth distribution metrics.

    Args:
        urls: List of URL strings

    Returns:
        Dictionary with depth distribution and statistics
    """
    depths = [get_path_depth(url) for url in urls]
    depth_counter = Counter(depths)

    if not depths:
        return {
            'distribution': {},
            'histogram': {},
            'average': 0,
            'median': 0,
            'max': 0,
            'min': 0,
            'total_urls': 0
        }

    total = len(depths)
    avg_depth = sum(depths) / total
    sorted_depths = sorted(depths)
    median_depth = sorted_depths[total // 2]

    return {
        'distribution': dict(sorted(depth_counter.items())),
        'histogram': dict(sorted(depth_counter.items())),
        'average': avg_depth,
        'median': median_depth,
        'max': max(depths),
        'min': min(depths),
        'total_urls': total
    }


def analyze_depth_patterns(data: List[Dict]) -> Dict:
    """
    Analyze depth-specific patterns including links, path lengths, and more.

    Args:
        data: List of URL dictionaries from JSONL with url, links, depth fields

    Returns:
        Dictionary with per-depth pattern analysis
    """
    depth_patterns = defaultdict(lambda: {
        'count': 0,
        'total_links': 0,
        'total_path_length': 0,
        'has_fragment': 0,
        'has_query': 0,
        'urls': []
    })

    for item in data:
        url = item.get('url', '')
        if not url:
            continue

        # Get depth from item or calculate it
        depth = item.get('depth')
        if depth is None:
            depth = get_path_depth(url)

        # Parse URL components
        components = parse_url_components(url)

        # Aggregate metrics per depth
        pattern = depth_patterns[depth]
        pattern['count'] += 1
        pattern['urls'].append(url)

        # Links
        links = item.get('links', [])
        pattern['total_links'] += len(links)

        # Path length
        pattern['total_path_length'] += len(components['path'])

        # Fragment
        if components['has_fragment']:
            pattern['has_fragment'] += 1

        # Query
        if components['has_query']:
            pattern['has_query'] += 1

    # Calculate averages and percentages
    result = {}
    for depth, pattern in depth_patterns.items():
        count = pattern['count']

        result[depth] = {
            'count': count,
            'avg_links': pattern['total_links'] / count if count > 0 else 0,
            'avg_path_length': pattern['total_path_length'] / count if count > 0 else 0,
            'fragment_percentage': (pattern['has_fragment'] / count * 100) if count > 0 else 0,
            'query_percentage': (pattern['has_query'] / count * 100) if count > 0 else 0,
            'sample_urls': pattern['urls'][:5]  # First 5 examples
        }

    return result


def analyze_depth_flow(data: List[Dict]) -> Dict:
    """
    Analyze how content flows across depth levels (children per parent).

    Args:
        data: List of URL dictionaries with parent-child relationships

    Returns:
        Dictionary with depth flow metrics
    """
    from collections import defaultdict

    # Build parent-child map
    parent_child_map = defaultdict(list)
    url_to_depth = {}

    for item in data:
        url = item.get('url', '')
        if not url:
            continue

        depth = item.get('depth')
        if depth is None:
            depth = get_path_depth(url)

        url_to_depth[url] = depth

        parent = item.get('parent_url')
        if parent and parent != url:
            parent_child_map[parent].append(url)

    # Calculate flow per depth
    depth_flow = defaultdict(lambda: {
        'count': 0,
        'children_list': []
    })

    for url, depth in url_to_depth.items():
        flow = depth_flow[depth]
        flow['count'] += 1

        children_count = len(parent_child_map.get(url, []))
        flow['children_list'].append(children_count)

    # Calculate statistics
    result = {}
    for depth, flow in depth_flow.items():
        children_list = flow['children_list']
        count = flow['count']

        result[depth] = {
            'count': count,
            'avg_children': sum(children_list) / count if count > 0 else 0,
            'max_children': max(children_list) if children_list else 0,
            'min_children': min(children_list) if children_list else 0,
            'total_children': sum(children_list)
        }

    return result


def compute_depth_health_score(urls: List[str], optimal_range: tuple = (2, 4)) -> Dict:
    """
    Compute health score based on optimal depth range.

    Args:
        urls: List of URL strings
        optimal_range: Tuple of (min_optimal, max_optimal) depth

    Returns:
        Dictionary with health metrics
    """
    depths = [get_path_depth(url) for url in urls]

    if not depths:
        return {
            'depth_score': 0,
            'optimal_count': 0,
            'too_shallow': 0,
            'too_deep': 0,
            'optimal_percentage': 0
        }

    min_optimal, max_optimal = optimal_range
    optimal_count = sum(1 for d in depths if min_optimal <= d <= max_optimal)
    too_shallow = sum(1 for d in depths if d < min_optimal)
    too_deep = sum(1 for d in depths if d > max_optimal)

    total = len(depths)
    optimal_percentage = (optimal_count / total * 100) if total > 0 else 0

    return {
        'depth_score': optimal_percentage,
        'optimal_count': optimal_count,
        'too_shallow': too_shallow,
        'too_deep': too_deep,
        'optimal_percentage': optimal_percentage,
        'total_urls': total
    }


def get_max_depth(data: List[Dict]) -> int:
    """
    Get the maximum depth from dataset.

    Args:
        data: List of URL dictionaries

    Returns:
        Maximum depth value
    """
    max_depth = 0

    for item in data:
        depth = item.get('depth')
        if depth is None:
            url = item.get('url', '')
            if url:
                depth = get_path_depth(url)
            else:
                continue

        if depth > max_depth:
            max_depth = depth

    return max_depth


def classify_depth_level(depth: int) -> str:
    """
    Classify a depth level as shallow, optimal, or deep.

    Args:
        depth: Depth value

    Returns:
        Classification string
    """
    if depth <= 1:
        return 'shallow'
    elif 2 <= depth <= 4:
        return 'optimal'
    elif 5 <= depth <= 7:
        return 'deep'
    else:
        return 'very_deep'
