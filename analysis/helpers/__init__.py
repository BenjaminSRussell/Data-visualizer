"""
Strategic Helper Function Library

This module provides five categories of helper functions that bridge gaps
in the current analysis system and provide deeper insights into URL patterns,
quality, and architecture.

Categories:
1. Semantic Clustering - Bridge syntactic and semantic understanding
2. Temporal Intelligence - Expose crawl patterns and content lifecycle
3. Graph Topology Validators - Validate architectural assumptions
4. Data Quality Forensics - Root cause analysis for quality issues
5. Multi-Dimensional Scoring - Context-aware composite metrics
"""

from .semantic_clustering import (
    calculate_semantic_distance,
    identify_content_archetypes,
    map_navigation_intent,
    cluster_by_function,
)

from .temporal_intelligence import (
    detect_crawl_waves,
    identify_content_freshness_zones,
    calculate_discovery_efficiency,
    map_discovery_lag_patterns,
)

from .graph_validators import (
    validate_topology_type,
    detect_architectural_antipatterns,
    validate_breadcrumb_consistency,
    identify_dark_matter_urls,
)

from .quality_forensics import (
    trace_duplication_source,
    identify_quality_degradation_points,
    map_parameter_pollution,
    detect_systematic_issues,
)

from .scoring_framework import (
    calculate_contextual_score,
    generate_comparative_scores,
    decompose_score,
    apply_domain_rubric,
)

__all__ = [
    # Semantic Clustering
    'calculate_semantic_distance',
    'identify_content_archetypes',
    'map_navigation_intent',
    'cluster_by_function',

    # Temporal Intelligence
    'detect_crawl_waves',
    'identify_content_freshness_zones',
    'calculate_discovery_efficiency',
    'map_discovery_lag_patterns',

    # Graph Validators
    'validate_topology_type',
    'detect_architectural_antipatterns',
    'validate_breadcrumb_consistency',
    'identify_dark_matter_urls',

    # Quality Forensics
    'trace_duplication_source',
    'identify_quality_degradation_points',
    'map_parameter_pollution',
    'detect_systematic_issues',

    # Scoring Framework
    'calculate_contextual_score',
    'generate_comparative_scores',
    'decompose_score',
    'apply_domain_rubric',
]
