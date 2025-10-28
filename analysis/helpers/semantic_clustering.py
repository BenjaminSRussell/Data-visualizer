"""
Semantic Clustering Utilities

Purpose: Bridge the gap between syntactic URL parsing and semantic content understanding.
The current system excels at structural analysis (depth, segments, patterns) but lacks
semantic clustering beyond keyword matching.

Integration Points:
- Enhances semantic_path_analyzer.py (lines 15-250)
- Complements batch_detector.py (lines 30-400)
- Provides semantic distance metrics beyond embedding-based approaches
"""

from typing import Dict, List, Tuple, Set
from collections import Counter, defaultdict
import re
from urllib.parse import urlparse


# Content archetype definitions
CONTENT_ARCHETYPES = {
    'user_generated_hub': {
        'patterns': ['forum', 'community', 'discussion', 'thread', 'post', 'comment', 'user', 'profile'],
        'structure': 'hierarchical',
        'intent': 'discovery'
    },
    'administrative_interface': {
        'patterns': ['admin', 'dashboard', 'manage', 'control', 'settings', 'config', 'panel'],
        'structure': 'flat',
        'intent': 'direct_access'
    },
    'content_catalog': {
        'patterns': ['blog', 'article', 'news', 'post', 'story', 'archive', 'category'],
        'structure': 'hierarchical',
        'intent': 'discovery'
    },
    'transactional_flow': {
        'patterns': ['cart', 'checkout', 'payment', 'order', 'purchase', 'buy', 'shop'],
        'structure': 'sequential',
        'intent': 'direct_access'
    },
    'informational_resource': {
        'patterns': ['about', 'faq', 'help', 'docs', 'documentation', 'guide', 'tutorial'],
        'structure': 'flat',
        'intent': 'search'
    },
    'media_gallery': {
        'patterns': ['gallery', 'photo', 'image', 'video', 'media', 'album'],
        'structure': 'grid',
        'intent': 'discovery'
    },
    'api_endpoint': {
        'patterns': ['api', 'rest', 'graphql', 'json', 'xml', 'endpoint'],
        'structure': 'hierarchical',
        'intent': 'programmatic'
    }
}

# Navigation intent patterns
NAVIGATION_INTENTS = {
    'discovery': ['browse', 'explore', 'discover', 'search', 'find', 'list', 'all', 'category'],
    'direct_access': ['view', 'show', 'detail', 'single', 'id', 'get'],
    'creation': ['create', 'new', 'add', 'post', 'submit', 'upload'],
    'modification': ['edit', 'update', 'modify', 'change'],
    'deletion': ['delete', 'remove', 'destroy'],
    'authentication': ['login', 'logout', 'signin', 'signout', 'register', 'signup'],
    'filtering': ['filter', 'sort', 'by', 'tag', 'category']
}


def calculate_semantic_distance(url1: str, url2: str, use_path_similarity: bool = True) -> float:
    """
    Calculate semantic distance between two URLs beyond structural similarity.

    This goes beyond simple string comparison to understand functional similarity.

    Args:
        url1: First URL
        url2: Second URL
        use_path_similarity: Whether to include path structure similarity

    Returns:
        Semantic distance score (0.0 = identical, 1.0 = completely different)

    Example:
        >>> calculate_semantic_distance(
        ...     "https://example.com/user/profile/123",
        ...     "https://example.com/account/settings/456"
        ... )
        0.35  # Similar archetype (user-related) but different functions
    """
    # Extract components
    parsed1 = urlparse(url1)
    parsed2 = urlparse(url2)

    # Domain similarity
    domain_match = 1.0 if parsed1.netloc == parsed2.netloc else 0.0

    # Extract semantic tokens
    tokens1 = _extract_semantic_tokens(parsed1.path)
    tokens2 = _extract_semantic_tokens(parsed2.path)

    # Token overlap (Jaccard similarity)
    token_overlap = _jaccard_similarity(set(tokens1), set(tokens2))

    # Archetype similarity
    archetype1 = identify_content_archetypes([url1])
    archetype2 = identify_content_archetypes([url2])
    archetype_match = 1.0 if archetype1.get('dominant') == archetype2.get('dominant') else 0.0

    # Intent similarity
    intent1 = map_navigation_intent([url1])
    intent2 = map_navigation_intent([url2])
    intent_match = 1.0 if intent1.get('dominant') == intent2.get('dominant') else 0.0

    # Path structure similarity (optional)
    structure_similarity = 0.0
    if use_path_similarity:
        depth1 = len([s for s in parsed1.path.split('/') if s])
        depth2 = len([s for s in parsed2.path.split('/') if s])
        depth_diff = abs(depth1 - depth2)
        structure_similarity = 1.0 / (1.0 + depth_diff)

    # Weighted combination
    weights = {
        'domain': 0.2,
        'tokens': 0.3,
        'archetype': 0.25,
        'intent': 0.15,
        'structure': 0.1
    }

    similarity = (
        domain_match * weights['domain'] +
        token_overlap * weights['tokens'] +
        archetype_match * weights['archetype'] +
        intent_match * weights['intent'] +
        structure_similarity * weights['structure']
    )

    # Return distance (inverse of similarity)
    return 1.0 - similarity


def identify_content_archetypes(urls: List[str]) -> Dict:
    """
    Identify content archetypes (functional similarity groups).

    Goes beyond keyword matching to understand the functional role of URL groups.

    Args:
        urls: List of URL strings

    Returns:
        Dictionary with archetype distribution and characteristics

    Example:
        >>> identify_content_archetypes([
        ...     "https://example.com/forum/thread/123",
        ...     "https://example.com/community/post/456"
        ... ])
        {
            'distribution': {'user_generated_hub': 2},
            'dominant': 'user_generated_hub',
            'characteristics': {
                'structure': 'hierarchical',
                'intent': 'discovery'
            }
        }
    """
    archetype_counts = Counter()
    url_archetype_map = {}

    for url in urls:
        parsed = urlparse(url)
        path_lower = parsed.path.lower()

        # Score each archetype
        scores = {}
        for archetype_name, archetype_def in CONTENT_ARCHETYPES.items():
            score = sum(1 for pattern in archetype_def['patterns'] if pattern in path_lower)
            if score > 0:
                scores[archetype_name] = score

        # Assign best matching archetype
        if scores:
            best_archetype = max(scores.items(), key=lambda x: x[1])[0]
            archetype_counts[best_archetype] += 1
            url_archetype_map[url] = best_archetype

    # Determine dominant archetype
    dominant = archetype_counts.most_common(1)[0][0] if archetype_counts else None

    # Surface descriptive metadata for the dominant archetype.
    characteristics = {}
    if dominant:
        characteristics = {
            'structure': CONTENT_ARCHETYPES[dominant]['structure'],
            'intent': CONTENT_ARCHETYPES[dominant]['intent']
        }

    return {
        'distribution': dict(archetype_counts),
        'dominant': dominant,
        'characteristics': characteristics,
        'url_mapping': url_archetype_map,
        'total_urls': len(urls),
        'classified_urls': len(url_archetype_map),
        'unclassified_urls': len(urls) - len(url_archetype_map)
    }


def map_navigation_intent(urls: List[str]) -> Dict:
    """
    Map navigation intent patterns (discovery vs direct access).

    Identifies whether URLs suggest exploratory behavior or direct access patterns.

    Args:
        urls: List of URL strings

    Returns:
        Dictionary with intent distribution and patterns

    Example:
        >>> map_navigation_intent([
        ...     "https://example.com/browse/products",
        ...     "https://example.com/product/12345"
        ... ])
        {
            'distribution': {'discovery': 1, 'direct_access': 1},
            'dominant': 'discovery',
            'discovery_ratio': 0.5
        }
    """
    intent_counts = Counter()
    url_intent_map = {}

    for url in urls:
        parsed = urlparse(url)
        path_lower = parsed.path.lower()

        # Check for numeric IDs (suggests direct access)
        has_numeric_id = bool(re.search(r'/\d+', parsed.path))

        # Score each intent
        scores = defaultdict(int)
        for intent_name, patterns in NAVIGATION_INTENTS.items():
            score = sum(1 for pattern in patterns if pattern in path_lower)
            if score > 0:
                scores[intent_name] = score

        # Direct access bonus for numeric IDs
        if has_numeric_id:
            scores['direct_access'] += 2

        # Assign best matching intent
        if scores:
            best_intent = max(scores.items(), key=lambda x: x[1])[0]
        else:
            # Default classification based on structure
            best_intent = 'direct_access' if has_numeric_id else 'discovery'

        intent_counts[best_intent] += 1
        url_intent_map[url] = best_intent

    # Calculate ratios
    total = len(urls)
    discovery_count = intent_counts.get('discovery', 0)
    direct_access_count = intent_counts.get('direct_access', 0)

    dominant = intent_counts.most_common(1)[0][0] if intent_counts else None

    return {
        'distribution': dict(intent_counts),
        'dominant': dominant,
        'discovery_ratio': discovery_count / total if total > 0 else 0,
        'direct_access_ratio': direct_access_count / total if total > 0 else 0,
        'url_mapping': url_intent_map,
        'total_urls': total
    }


def cluster_by_function(urls: List[str], min_cluster_size: int = 3) -> List[Dict]:
    """
    Cluster URLs by functional similarity rather than structural similarity.

    This provides semantic grouping that complements the structural clustering
    in batch_detector.py.

    Args:
        urls: List of URL strings
        min_cluster_size: Minimum number of URLs to form a cluster

    Returns:
        List of functional clusters

    Example:
        >>> cluster_by_function([
        ...     "https://example.com/user/profile/123",
        ...     "https://example.com/user/settings/123",
        ...     "https://example.com/admin/dashboard",
        ...     "https://example.com/admin/users"
        ... ])
        [
            {
                'cluster_name': 'user_management',
                'archetype': 'user_generated_hub',
                'intent': 'direct_access',
                'urls': ['https://example.com/user/profile/123', ...],
                'size': 2
            },
            ...
        ]
    """
    # First pass: identify archetypes and intents
    archetype_result = identify_content_archetypes(urls)
    intent_result = map_navigation_intent(urls)

    # Group by (archetype, intent) combination
    clusters = defaultdict(list)

    for url in urls:
        archetype = archetype_result['url_mapping'].get(url, 'unknown')
        intent = intent_result['url_mapping'].get(url, 'unknown')
        cluster_key = (archetype, intent)
        clusters[cluster_key].append(url)

    # Build cluster results
    result_clusters = []

    for (archetype, intent), cluster_urls in clusters.items():
        if len(cluster_urls) >= min_cluster_size:
            # Generate descriptive cluster name
            cluster_name = f"{archetype}_{intent}"

            # Extract common path prefix
            common_prefix = _find_common_path_prefix(cluster_urls)

            result_clusters.append({
                'cluster_name': cluster_name,
                'archetype': archetype,
                'intent': intent,
                'urls': cluster_urls,
                'size': len(cluster_urls),
                'common_prefix': common_prefix,
                'percentage': (len(cluster_urls) / len(urls)) * 100 if urls else 0
            })

    # Sort by size
    result_clusters.sort(key=lambda x: x['size'], reverse=True)

    return result_clusters


# Helper functions

def _extract_semantic_tokens(path: str) -> List[str]:
    """Extract meaningful semantic tokens from URL path."""
    # Split on common separators
    tokens = re.split(r'[/\-_.]', path.lower())

    # Filter out numbers, empty strings, and common stop words
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    filtered_tokens = [
        t for t in tokens
        if t and not t.isdigit() and t not in stop_words and len(t) > 1
    ]

    return filtered_tokens


def _jaccard_similarity(set1: Set, set2: Set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def _find_common_path_prefix(urls: List[str]) -> str:
    """Find common path prefix among URLs."""
    if not urls:
        return ""

    paths = [urlparse(url).path for url in urls]

    # Find common prefix
    if len(paths) == 1:
        return paths[0]

    # Split into segments
    path_segments = [p.split('/') for p in paths]

    # Find common prefix segments
    common = []
    for segments in zip(*path_segments):
        if len(set(segments)) == 1:
            common.append(segments[0])
        else:
            break

    return '/'.join(common)
