"""
Analysis Utilities - Shared Helper Modules

This package contains shared utility functions that eliminate code
redundancy across multiple analyzer modules.
"""

from .general_metrics import (
    analyze_depth_flow,
    analyze_depth_patterns,
    calculate_depth_distribution,
    classify_depth_level,
    compute_depth_health_score,
    get_max_depth,
)
from .url_utilities import (
    classify_fragment,
    count_fragments,
    extract_file_extension,
    extract_fragment,
    extract_path_segments,
    get_base_url,
    get_depth_distribution,
    get_path_depth,
    get_path_length,
    get_query_param_count,
    is_internal_link,
    is_same_domain,
    parse_url_components,
    resolve_link,
)

__all__ = [
    # URL Utilities
    "parse_url_components",
    "get_path_depth",
    "get_base_url",
    "is_same_domain",
    "is_internal_link",
    "resolve_link",
    "extract_fragment",
    "count_fragments",
    "classify_fragment",
    "extract_file_extension",
    "get_depth_distribution",
    "extract_path_segments",
    "get_query_param_count",
    "get_path_length",
    # General Metrics
    "calculate_depth_distribution",
    "analyze_depth_patterns",
    "analyze_depth_flow",
    "compute_depth_health_score",
    "get_max_depth",
    "classify_depth_level",
]
