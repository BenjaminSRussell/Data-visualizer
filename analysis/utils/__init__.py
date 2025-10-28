"""
Analysis Utilities - Shared Helper Modules

This package contains shared utility functions that eliminate code
redundancy across multiple analyzer modules.
"""

from .url_utilities import (
    parse_url_components,
    get_path_depth,
    get_base_url,
    is_same_domain,
    is_internal_link,
    resolve_link,
    extract_fragment,
    count_fragments,
    classify_fragment,
    extract_file_extension,
    get_depth_distribution,
    extract_path_segments,
    get_query_param_count,
    get_path_length
)

from .general_metrics import (
    calculate_depth_distribution,
    analyze_depth_patterns,
    analyze_depth_flow,
    compute_depth_health_score,
    get_max_depth,
    classify_depth_level
)

__all__ = [
    # URL Utilities
    'parse_url_components',
    'get_path_depth',
    'get_base_url',
    'is_same_domain',
    'is_internal_link',
    'resolve_link',
    'extract_fragment',
    'count_fragments',
    'classify_fragment',
    'extract_file_extension',
    'get_depth_distribution',
    'extract_path_segments',
    'get_query_param_count',
    'get_path_length',
    # General Metrics
    'calculate_depth_distribution',
    'analyze_depth_patterns',
    'analyze_depth_flow',
    'compute_depth_health_score',
    'get_max_depth',
    'classify_depth_level'
]
