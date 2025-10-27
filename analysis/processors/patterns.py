"""Detect patterns in URL collections: file types, structures, depth, domains."""

from collections import Counter
import re
import logging
from typing import Dict, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def execute(urls: List[str]) -> Dict[str, any]:
    """Analyze URL list for file types, structures, prefixes, depth, and domains."""
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
                result['domain_distribution'][parsed.netloc] += 1
                path = parsed.path
                if '.' in path:
                    extension = path.split('.')[-1].lower()
                    if extension in ['html', 'htm', 'php', 'asp', 'jsp', 'pdf',
                                    'jpg', 'png', 'gif', 'css', 'js', 'xml']:
                        result['file_types'][extension] += 1
                if path and path != '/':
                    depth = len([p for p in path.split('/') if p])
                    result['depth_distribution'][depth] += 1
                else:
                    result['depth_distribution'][0] += 1
                if path:
                    paths.append(path)
                    if re.search(r'/\d{4}(/\d{2})?(/\d{2})?/', path):
                        result['url_structures']['has_date'].append(url)
                    if re.search(r'/\d+/', path) or re.search(r'id=\d+', url):
                        result['url_structures']['has_id'].append(url)
                    if re.search(r'/[a-z]+-[a-z-]+', path):
                        result['url_structures']['has_slug'].append(url)
                    if path.count('/') >= 3:
                        result['url_structures']['hierarchical'].append(url)
            except Exception as e:
                logger.warning(f"Error analyzing URL {url}: {e}")
                continue
        if paths:
            result['common_prefixes'] = _find_common_prefixes(paths)
    except Exception as e:
        logger.error(f"Error detecting patterns: {e}")

    return result


def _find_common_prefixes(paths: List[str], min_count: int = 3) -> List[str]:
    """Find path prefixes occurring at least min_count times."""
    prefix_counter = Counter()

    for path in paths:
        parts = [p for p in path.split('/') if p]
        for i in range(1, len(parts)):
            prefix = '/' + '/'.join(parts[:i])
            prefix_counter[prefix] += 1
    common = [prefix for prefix, count in prefix_counter.items()
              if count >= min_count]

    return sorted(common, key=lambda x: prefix_counter[x], reverse=True)


def summarize(patterns: Dict[str, any]) -> Dict[str, any]:
    """Generate summary statistics from pattern detection results."""
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
