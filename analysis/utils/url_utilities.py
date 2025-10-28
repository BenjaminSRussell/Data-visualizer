"""
URL Utilities - Shared URL Parsing and Analysis Functions

Purpose: Single source of truth for all URL parsing, decomposition, and
         basic analysis operations. Eliminates redundant parsing logic
         across multiple analyzer modules.
"""

from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin, unquote
from collections import Counter


def parse_url_components(url: str) -> Dict:
    """
    Parse all components from a URL.

    Args:
        url: URL string to parse

    Returns:
        Dictionary containing all parsed components
    """
    try:
        parsed = urlparse(url)

        # Extract path segments (non-empty)
        path_segments = [s for s in parsed.path.split('/') if s]

        return {
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'hostname': parsed.hostname,
            'port': parsed.port,
            'username': parsed.username,
            'password': parsed.password,
            'path': parsed.path,
            'path_segments': path_segments,
            'path_depth': len(path_segments),
            'query': parsed.query,
            'fragment': parsed.fragment,
            'has_auth': bool(parsed.username),
            'has_port': bool(parsed.port),
            'has_query': bool(parsed.query),
            'has_fragment': bool(parsed.fragment)
        }
    except (ValueError, AttributeError, TypeError):
        return {
            'scheme': '',
            'netloc': '',
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
            'path': '',
            'path_segments': [],
            'path_depth': 0,
            'query': '',
            'fragment': '',
            'has_auth': False,
            'has_port': False,
            'has_query': False,
            'has_fragment': False
        }


def get_path_depth(url_or_path: str) -> int:
    """
    Calculate the depth of a URL or path (number of path segments).

    Args:
        url_or_path: Full URL or just the path component

    Returns:
        Number of non-empty path segments
    """
    # Check if it looks like a full URL
    if '://' in url_or_path:
        parsed = urlparse(url_or_path)
        path = parsed.path
    else:
        path = url_or_path

    segments = [s for s in path.split('/') if s]
    return len(segments)


def get_base_url(url: str) -> str:
    """
    Extract the base URL (scheme + netloc).

    Args:
        url: Full URL

    Returns:
        Base URL (e.g., "https://example.com")
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs belong to the same domain.

    Args:
        url1: First URL
        url2: Second URL

    Returns:
        True if both URLs have the same netloc
    """
    if not url1 or not url2:
        return False

    try:
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
    except (ValueError, AttributeError, TypeError):
        return False

    return domain1 == domain2


def is_internal_link(source_url: str, target_url: str) -> bool:
    """
    Check if a link is internal (same domain as source).

    Args:
        source_url: Source URL
        target_url: Target URL

    Returns:
        True if target is internal to source domain
    """
    return is_same_domain(source_url, target_url)


def resolve_link(link: str, source_url: str, base_url: Optional[str] = None) -> Optional[str]:
    """
    Resolve a link (relative or absolute) to an absolute URL.

    Args:
        link: Link to resolve (can be relative, absolute, protocol-relative)
        source_url: The URL where the link was found
        base_url: Optional base URL (will be extracted from source_url if not provided)

    Returns:
        Resolved absolute URL, or None if link is invalid
    """
    if not link:
        return None

    # Skip fragment-only links
    if link.startswith('#'):
        return None

    # Protocol-relative URLs
    if link.startswith('//'):
        return 'https:' + link

    # Root-relative URLs
    if link.startswith('/'):
        if base_url is None:
            base_url = get_base_url(source_url)
        return urljoin(base_url, link)

    # Absolute URLs
    if link.startswith('http'):
        return link

    # Relative URLs
    return urljoin(source_url, link)


def extract_fragment(url: str) -> Optional[str]:
    """
    Extract and decode the fragment from a URL.

    Args:
        url: URL string

    Returns:
        Decoded fragment string, or None if no fragment
    """
    parsed = urlparse(url)
    if parsed.fragment:
        return unquote(parsed.fragment)
    return None


def count_fragments(urls: List[str]) -> Dict:
    """
    Count fragment occurrences across multiple URLs.

    Args:
        urls: List of URL strings

    Returns:
        Dictionary with fragment statistics
    """
    fragment_counter = Counter()
    urls_with_fragments = 0

    for url in urls:
        fragment = extract_fragment(url)
        if fragment:
            urls_with_fragments += 1
            fragment_counter[fragment] += 1

    return {
        'total_urls': len(urls),
        'urls_with_fragments': urls_with_fragments,
        'unique_fragments': len(fragment_counter),
        'fragment_distribution': dict(fragment_counter),
        'fragment_percentage': (urls_with_fragments / len(urls) * 100) if urls else 0
    }


def classify_fragment(fragment: str) -> str:
    """
    Classify a fragment as anchor, route, or other.

    Args:
        fragment: Fragment string (without #)

    Returns:
        Classification: 'anchor', 'route', or 'other'
    """
    import re

    # Anchor links (simple ID selectors)
    if re.match(r'^[a-zA-Z][\w-]*$', fragment):
        return 'anchor'

    # Client-side routes
    if re.match(r'^(/|#/).*', fragment):
        return 'route'

    return 'other'


def extract_file_extension(url_or_path: str) -> Optional[str]:
    """
    Extract file extension from URL or path.

    Args:
        url_or_path: URL or path string

    Returns:
        Lowercase file extension (without dot), or None if no extension
    """
    # Extract the path from absolute URLs before checking for extensions.
    if '://' in url_or_path:
        parsed = urlparse(url_or_path)
        path = parsed.path
    else:
        path = url_or_path

    # Remove query and fragment
    path = path.split('?')[0].split('#')[0]

    if '.' in path:
        parts = path.split('.')
        if len(parts) > 1:
            ext = parts[-1].lower()
            # Validate: should be alphanumeric and reasonable length
            if ext.isalnum() and len(ext) <= 10:
                return ext

    return None


def get_depth_distribution(urls: List[str]) -> Dict:
    """
    Calculate depth distribution across multiple URLs.

    Args:
        urls: List of URL strings

    Returns:
        Dictionary with depth statistics
    """
    depths = [get_path_depth(url) for url in urls]
    depth_counter = Counter(depths)

    total = len(depths)
    avg_depth = sum(depths) / total if total > 0 else 0
    max_depth = max(depths) if depths else 0
    min_depth = min(depths) if depths else 0

    return {
        'distribution': dict(sorted(depth_counter.items())),
        'average': avg_depth,
        'max': max_depth,
        'min': min_depth,
        'total_urls': total
    }


def extract_path_segments(url: str) -> List[str]:
    """
    Extract non-empty path segments from a URL.

    Args:
        url: URL string

    Returns:
        List of path segments
    """
    parsed = urlparse(url)
    return [s for s in parsed.path.split('/') if s]


def get_query_param_count(url: str) -> int:
    """
    Count the number of query parameters in a URL.

    Args:
        url: URL string

    Returns:
        Number of query parameters
    """
    parsed = urlparse(url)
    if parsed.query:
        return len(parsed.query.split('&'))
    return 0


def get_path_length(url: str) -> int:
    """
    Get the character length of the path component.

    Args:
        url: URL string

    Returns:
        Length of path string
    """
    parsed = urlparse(url)
    return len(parsed.path)
