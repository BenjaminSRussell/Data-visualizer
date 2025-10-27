"""
Operation: Detect Patterns

Purpose: Detect patterns in a collection of URLs
Input: List of URLs
Output: Dictionary of detected patterns
Dependencies: collections, re
"""

from collections import Counter
import re
import logging
from typing import Dict, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def execute(urls: List[str]) -> Dict[str, any]:
    """
    Detect patterns across a collection of URLs.

    Args:
        urls: List of URL strings to analyze

    Returns:
        Dictionary with:
            - file_types: Counter of file extensions
            - url_structures: Dict of structural patterns
            - common_prefixes: List of common path prefixes
            - depth_distribution: Counter of URL depths
            - domain_distribution: Counter of domains

    Example:
        patterns = execute(url_list)
        print(f"Most common file type: {patterns['file_types'].most_common(1)}")
    """
    result = {
        'file_types': Counter(),
        'url_structures': {
            'has_date': [],
            'has_id': [],
            'has_slug': [],
            'hierarchical': []
        },
        'common_prefixes': [],
        'depth_distribution': Counter(),
        'domain_distribution': Counter()
    }

    if not urls:
        return result

    try:
        paths = []

        for url in urls:
            try:
                parsed = urlparse(url)

                # Domain distribution
                result['domain_distribution'][parsed.netloc] += 1

                # File type detection
                path = parsed.path
                if '.' in path:
                    extension = path.split('.')[-1].lower()
                    # Only count common web extensions
                    if extension in ['html', 'htm', 'php', 'asp', 'jsp', 'pdf',
                                    'jpg', 'png', 'gif', 'css', 'js', 'xml']:
                        result['file_types'][extension] += 1

                # Depth
                if path and path != '/':
                    depth = len([p for p in path.split('/') if p])
                    result['depth_distribution'][depth] += 1
                else:
                    result['depth_distribution'][0] += 1

                # URL structure patterns
                if path:
                    paths.append(path)

                    # Date pattern (YYYY, YYYY/MM, YYYY/MM/DD)
                    if re.search(r'/\d{4}(/\d{2})?(/\d{2})?/', path):
                        result['url_structures']['has_date'].append(url)

                    # ID pattern (numbers in path)
                    if re.search(r'/\d+/', path) or re.search(r'id=\d+', url):
                        result['url_structures']['has_id'].append(url)

                    # Slug pattern (hyphenated lowercase)
                    if re.search(r'/[a-z]+-[a-z-]+', path):
                        result['url_structures']['has_slug'].append(url)

                    # Hierarchical (3+ levels)
                    if path.count('/') >= 3:
                        result['url_structures']['hierarchical'].append(url)

            except Exception as e:
                logger.warning(f"Error analyzing URL {url}: {e}")
                continue

        # Find common prefixes
        if paths:
            result['common_prefixes'] = _find_common_prefixes(paths)

    except Exception as e:
        logger.error(f"Error detecting patterns: {e}")

    return result


def _find_common_prefixes(paths: List[str], min_count: int = 3) -> List[str]:
    """
    Find common path prefixes.

    Args:
        paths: List of URL paths
        min_count: Minimum occurrence count to be considered common

    Returns:
        List of common prefix strings
    """
    prefix_counter = Counter()

    for path in paths:
        parts = [p for p in path.split('/') if p]

        # Check all possible prefixes
        for i in range(1, len(parts)):
            prefix = '/' + '/'.join(parts[:i])
            prefix_counter[prefix] += 1

    # Return prefixes that appear at least min_count times
    common = [prefix for prefix, count in prefix_counter.items()
              if count >= min_count]

    return sorted(common, key=lambda x: prefix_counter[x], reverse=True)


def summarize(patterns: Dict[str, any]) -> Dict[str, any]:
    """
    Create a summary of detected patterns.

    Args:
        patterns: Output from execute()

    Returns:
        Dictionary with pattern summary statistics

    Example:
        patterns = execute(urls)
        summary = summarize(patterns)
        print(f"Total file types: {summary['file_types_count']}")
    """
    return {
        'file_types_count': len(patterns['file_types']),
        'most_common_file_type': patterns['file_types'].most_common(1)[0]
        if patterns['file_types'] else None,

        'structure_patterns_count': sum(
            len(v) for v in patterns['url_structures'].values()
        ),

        'urls_with_dates': len(patterns['url_structures']['has_date']),
        'urls_with_ids': len(patterns['url_structures']['has_id']),
        'urls_with_slugs': len(patterns['url_structures']['has_slug']),
        'hierarchical_urls': len(patterns['url_structures']['hierarchical']),

        'common_prefixes_count': len(patterns['common_prefixes']),
        'unique_domains': len(patterns['domain_distribution']),

        'depth_stats': {
            'min': min(patterns['depth_distribution'].keys())
            if patterns['depth_distribution'] else 0,
            'max': max(patterns['depth_distribution'].keys())
            if patterns['depth_distribution'] else 0,
            'distribution': dict(patterns['depth_distribution'])
        }
    }
