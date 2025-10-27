"""Extract structural features from URLs."""

from urllib.parse import urlparse, parse_qs
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def execute(url: str) -> Dict[str, any]:
    """Extract URL components: scheme, domain, subdomain, path, depth, extension, query params, fragment."""
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
        result['query_params'] = parse_qs(parsed.query)
        if parsed.netloc:
            parts = parsed.netloc.split('.')
            if len(parts) > 2:
                result['subdomain'] = '.'.join(parts[:-2])

        if parsed.path and parsed.path != '/':
            clean_path = parsed.path.strip('/')
            if clean_path:
                result['path_segments'] = clean_path.split('/')
                result['depth'] = len(result['path_segments'])
                last_segment = result['path_segments'][-1]
                if '.' in last_segment:
                    result['file_extension'] = last_segment.split('.')[-1].lower()
        else:
            result['is_homepage'] = True
    except Exception as e:
        logger.error(f"Error extracting features from {url}: {e}")

    return result
