"""
Operation: Extract URL Features

Purpose: Extract structural features from a URL
Input: URL string
Output: Dictionary of URL features (domain, path, extension, etc.)
Dependencies: urllib
"""

from urllib.parse import urlparse, parse_qs
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def execute(url: str) -> Dict[str, any]:
    """
    Extract structural features from a URL.

    Args:
        url: URL string to analyze

    Returns:
        Dictionary with:
            - url: Original URL
            - scheme: URL scheme (http, https)
            - domain: Domain name
            - subdomain: Subdomain (if any)
            - path: URL path
            - depth: Path depth (number of slashes)
            - file_extension: File extension (if any)
            - query_params: Dictionary of query parameters
            - fragment: URL fragment
            - is_homepage: Boolean indicating if this is a homepage
            - path_segments: List of path segments

    Example:
        features = execute("https://example.com/blog/post.html?id=123")
        print(f"Domain: {features['domain']}")
        print(f"Extension: {features['file_extension']}")
    """
    result = {
        'url': url,
        'scheme': None,
        'domain': None,
        'subdomain': None,
        'path': None,
        'depth': 0,
        'file_extension': None,
        'query_params': {},
        'fragment': None,
        'is_homepage': False,
        'path_segments': []
    }

    try:
        parsed = urlparse(url)

        result['scheme'] = parsed.scheme
        result['domain'] = parsed.netloc
        result['path'] = parsed.path
        result['fragment'] = parsed.fragment

        # Query parameters
        result['query_params'] = parse_qs(parsed.query)

        # Subdomain extraction
        if parsed.netloc:
            parts = parsed.netloc.split('.')
            if len(parts) > 2:
                result['subdomain'] = '.'.join(parts[:-2])

        # Path analysis
        if parsed.path and parsed.path != '/':
            # Remove leading/trailing slashes for analysis
            clean_path = parsed.path.strip('/')

            # Path segments
            if clean_path:
                result['path_segments'] = clean_path.split('/')
                result['depth'] = len(result['path_segments'])

                # File extension
                last_segment = result['path_segments'][-1]
                if '.' in last_segment:
                    result['file_extension'] = last_segment.split('.')[-1].lower()
        else:
            result['is_homepage'] = True

    except Exception as e:
        logger.error(f"Error extracting features from {url}: {e}")

    return result
