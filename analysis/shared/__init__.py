"""
Shared Analysis Components

This package contains shared components that eliminate redundancy
across analyzer modules.
"""

from .url_components import (
    URLComponentCache,
    bulk_parse_urls,
    get_cache_stats,
    get_components,
    get_normalized_url,
    get_url_cache,
)

__all__ = [
    "URLComponentCache",
    "get_url_cache",
    "get_components",
    "get_normalized_url",
    "bulk_parse_urls",
    "get_cache_stats",
]
