"""
URL Component Cache - Single Source of Truth for URL Parsing

Purpose: Parse each URL exactly ONCE and cache all components.
         Eliminates redundant parsing across multiple analyzers.

This is the CANONICAL source for all URL component extraction.
All analyzers should use this instead of parsing URLs themselves.
"""

from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs, unquote


class URLComponentCache:
    """
    Cache that parses each URL exactly once and stores all components.

    Eliminates redundant URL parsing across multiple analyzer modules.
    All URL analysis should go through this cache.
    """

    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._parse_count = 0
        self._cache_hits = 0

    def get_components(self, url: str) -> Dict:
        """
        Get all components for a URL. Returns cached result if available,
        otherwise parses and caches.

        Args:
            url: URL string to parse

        Returns:
            Dictionary containing all URL components:
                - url: Original URL
                - scheme: URL scheme (http, https, etc)
                - netloc: Full network location
                - hostname: Hostname only
                - domain: Domain (without subdomain)
                - subdomain: Subdomain if present
                - port: Port number if specified
                - path: Full path
                - path_normalized: Path without trailing slash
                - depth: Path depth (segment count)
                - segments: List of path segments
                - extension: File extension if present
                - query: Raw query string
                - query_params: Parsed query parameters
                - query_normalized: Query string with sorted params
                - fragment: URL fragment
                - has_auth: Boolean - has authentication
                - has_port: Boolean - has explicit port
                - has_query: Boolean - has query parameters
                - has_fragment: Boolean - has fragment
                - url_length: Total URL length
                - is_root: Boolean - is root URL
                - is_file: Boolean - has file extension
        """
        # Check cache first
        if url in self._cache:
            self._cache_hits += 1
            return self._cache[url]

        # Parse and cache
        self._parse_count += 1
        components = self._parse_url(url)
        self._cache[url] = components
        return components

    def _parse_url(self, url: str) -> Dict:
        """Parse URL and extract all components in one pass."""
        try:
            parsed = urlparse(url)

            # Basic components
            scheme = parsed.scheme or ''
            netloc = parsed.netloc or ''
            hostname = parsed.hostname or ''
            port = parsed.port
            path = parsed.path or ''
            query = parsed.query or ''
            fragment = parsed.fragment or ''

            # Domain decomposition
            domain, subdomain = self._extract_domain_parts(hostname)

            # Path analysis
            path_normalized = path.rstrip('/')
            segments = [s for s in path.split('/') if s]
            depth = len(segments)
            extension = self._extract_extension(path)

            # Query analysis
            query_params = parse_qs(query, keep_blank_values=True) if query else {}
            query_normalized = self._normalize_query(query_params)

            # Fragment analysis
            fragment_decoded = unquote(fragment) if fragment else ''

            # Boolean flags
            has_auth = bool(parsed.username)
            has_port = bool(port)
            has_query = bool(query)
            has_fragment = bool(fragment)

            # Derived properties
            url_length = len(url)
            is_root = depth == 0 or path in ('/', '')
            is_file = extension is not None

            return {
                # Original
                'url': url,

                # Basic components
                'scheme': scheme,
                'netloc': netloc,
                'hostname': hostname,
                'domain': domain,
                'subdomain': subdomain,
                'port': port,

                # Path components
                'path': path,
                'path_normalized': path_normalized,
                'depth': depth,
                'segments': segments,
                'extension': extension,

                # Query components
                'query': query,
                'query_params': query_params,
                'query_normalized': query_normalized,

                # Fragment components
                'fragment': fragment,
                'fragment_decoded': fragment_decoded,

                # Boolean flags
                'has_auth': has_auth,
                'has_port': has_port,
                'has_query': has_query,
                'has_fragment': has_fragment,

                # Derived properties
                'url_length': url_length,
                'is_root': is_root,
                'is_file': is_file
            }

        except Exception as e:
            # Provide minimal component structure when parsing fails.
            return {
                'url': url,
                'scheme': '',
                'netloc': '',
                'hostname': '',
                'domain': '',
                'subdomain': '',
                'port': None,
                'path': '',
                'path_normalized': '',
                'depth': 0,
                'segments': [],
                'extension': None,
                'query': '',
                'query_params': {},
                'query_normalized': '',
                'fragment': '',
                'fragment_decoded': '',
                'has_auth': False,
                'has_port': False,
                'has_query': False,
                'has_fragment': False,
                'url_length': len(url),
                'is_root': True,
                'is_file': False,
                'error': str(e)
            }

    def _extract_domain_parts(self, hostname: str) -> tuple:
        """
        Extract domain and subdomain from hostname.

        Returns:
            (domain, subdomain) tuple
        """
        if not hostname:
            return '', ''

        parts = hostname.split('.')

        # Handle common TLDs
        if len(parts) >= 2:
            # Simple heuristic: last two parts are domain (example.com)
            domain = '.'.join(parts[-2:])
            subdomain = '.'.join(parts[:-2]) if len(parts) > 2 else ''
            return domain, subdomain

        return hostname, ''

    def _extract_extension(self, path: str) -> Optional[str]:
        """Extract file extension from path."""
        if not path or '.' not in path:
            return None

        # Remove query and fragment
        path = path.split('?')[0].split('#')[0]

        # Use the last path segment to isolate the extension candidate.
        filename = path.split('/')[-1]

        if '.' in filename:
            ext = filename.split('.')[-1].lower()
            # Validate: alphanumeric and reasonable length
            if ext.isalnum() and len(ext) <= 10:
                return ext

        return None

    def _normalize_query(self, query_params: Dict) -> str:
        """Normalize query string by sorting parameters."""
        if not query_params:
            return ''

        # Sort parameters alphabetically
        sorted_items = sorted(query_params.items())

        # Build normalized query string
        parts = []
        for key, values in sorted_items:
            for value in values:
                parts.append(f"{key}={value}")

        return '&'.join(parts)

    def get_normalized_url(self, url: str, remove_fragment: bool = True,
                          remove_tracking: bool = True) -> str:
        """
        Get normalized version of URL for deduplication.

        Args:
            url: URL to normalize
            remove_fragment: Remove fragment identifier
            remove_tracking: Remove tracking parameters

        Returns:
            Normalized URL string
        """
        components = self.get_components(url)

        # Start with scheme and netloc
        normalized = f"{components['scheme']}://{components['netloc']}"

        # Add normalized path (no trailing slash unless root)
        path = components['path_normalized']
        if path:
            normalized += path
        elif not path or path == '/':
            normalized += '/'

        # Add query (optionally filter tracking params)
        if components['has_query']:
            if remove_tracking:
                filtered_params = self._remove_tracking_params(components['query_params'])
                if filtered_params:
                    query_str = self._normalize_query(filtered_params)
                    normalized += f"?{query_str}"
            else:
                normalized += f"?{components['query_normalized']}"

        # Add fragment (optional)
        if not remove_fragment and components['has_fragment']:
            normalized += f"#{components['fragment']}"

        return normalized

    def _remove_tracking_params(self, query_params: Dict) -> Dict:
        """Remove common tracking parameters."""
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', '_ga', '_gl', 'mc_cid', 'mc_eid',
            'ref', 'source', 'campaign', 'ad_id', 'ad_name'
        }

        return {
            k: v for k, v in query_params.items()
            if k.lower() not in tracking_params
        }

    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics."""
        total_requests = self._parse_count + self._cache_hits
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_size': len(self._cache),
            'parse_count': self._parse_count,
            'cache_hits': self._cache_hits,
            'total_requests': total_requests,
            'hit_rate_percent': hit_rate
        }

    def bulk_parse(self, urls: List[str]) -> None:
        """Pre-populate cache with multiple URLs."""
        for url in urls:
            if url not in self._cache:
                self.get_components(url)

    def clear_cache(self) -> None:
        """Clear the component cache."""
        self._cache.clear()
        self._parse_count = 0
        self._cache_hits = 0


# Global singleton instance
_global_cache = None


def get_url_cache() -> URLComponentCache:
    """Get the global URL component cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = URLComponentCache()
    return _global_cache


def get_components(url: str) -> Dict:
    """Convenience function to get components from global cache."""
    return get_url_cache().get_components(url)


def get_normalized_url(url: str, remove_fragment: bool = True,
                       remove_tracking: bool = True) -> str:
    """Convenience function to get normalized URL."""
    return get_url_cache().get_normalized_url(url, remove_fragment, remove_tracking)


def bulk_parse_urls(urls: List[str]) -> None:
    """Convenience function to bulk parse URLs."""
    get_url_cache().bulk_parse(urls)


def get_cache_stats() -> Dict:
    """Convenience function to get cache stats."""
    return get_url_cache().get_cache_stats()
