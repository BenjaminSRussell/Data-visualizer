"""
Graph Topology Validators

Purpose: Validate assumptions about site architecture through graph-theoretic proofs.
The network analyzer (network_analyzer.py:1-500) computes metrics but doesn't validate
whether the observed topology matches declared architecture.

Integration Points:
- Extends network_analyzer.py (lines 180-220) centrality calculations
- Validates architectural assumptions rather than just computing metrics
- Identifies antipatterns and architectural inconsistencies
"""

from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, Counter
from urllib.parse import urlparse
import numpy as np


def validate_topology_type(data: List[Dict], expected_topology: Optional[str] = None) -> Dict:
    """
    Verify hub-and-spoke vs mesh topology claims.

    Lines 180-220 in network_analyzer.py calculate centrality but don't question
    whether high-centrality pages are intentional hubs or accidental bottlenecks.

    Args:
        data: List of URL dictionaries with links
        expected_topology: Expected topology type ('hub-spoke', 'mesh', 'hierarchical', 'flat')

    Returns:
        Dictionary with topology validation results

    Example:
        {
            'detected_topology': 'hub-spoke',
            'confidence': 0.85,
            'matches_expected': True,
            'characteristics': {
                'hub_count': 5,
                'avg_hub_connections': 50,
                'network_centralization': 0.72
            }
        }
    """
    if not data:
        return {
            'detected_topology': None,
            'confidence': 0,
            'available': False
        }

    # Build graph
    graph = defaultdict(set)
    reverse_graph = defaultdict(set)
    all_urls = set()

    for item in data:
        url = item.get('url', '')
        if not url:
            continue

        all_urls.add(url)
        links = item.get('links', [])

        for link in links:
            if link and link in all_urls:
                graph[url].add(link)
                reverse_graph[link].add(url)

    # Calculate degree distribution
    in_degrees = [len(reverse_graph.get(url, set())) for url in all_urls]
    out_degrees = [len(graph.get(url, set())) for url in all_urls]

    # Topology detection metrics
    in_degree_std = np.std(in_degrees) if in_degrees else 0
    out_degree_std = np.std(out_degrees) if out_degrees else 0
    avg_in_degree = np.mean(in_degrees) if in_degrees else 0
    avg_out_degree = np.mean(out_degrees) if out_degrees else 0

    # Calculate network centralization (Freeman's centralization)
    max_in_degree = max(in_degrees) if in_degrees else 0
    max_out_degree = max(out_degrees) if out_degrees else 0
    n = len(all_urls)

    if n > 1:
        in_centralization = sum(max_in_degree - d for d in in_degrees) / ((n - 1) * (n - 2))
        out_centralization = sum(max_out_degree - d for d in out_degrees) / ((n - 1) * (n - 2))
    else:
        in_centralization = 0
        out_centralization = 0

    # Detect hubs (top 5% by in-degree)
    hub_threshold = np.percentile(in_degrees, 95) if in_degrees else 0
    hubs = [url for url in all_urls if len(reverse_graph.get(url, set())) >= hub_threshold]

    # Topology classification logic
    topology_scores = {
        'hub-spoke': 0.0,
        'mesh': 0.0,
        'hierarchical': 0.0,
        'flat': 0.0
    }

    # Hub-and-spoke: High centralization, few hubs with many connections
    if in_centralization > 0.6 and len(hubs) < len(all_urls) * 0.1:
        topology_scores['hub-spoke'] = 0.8 + (in_centralization * 0.2)

    # Mesh: Low centralization, relatively uniform degree distribution
    if in_centralization < 0.3 and in_degree_std < avg_in_degree:
        topology_scores['mesh'] = 0.7 + (0.3 - in_centralization)

    # Hierarchical: Moderate centralization, depth-based structure
    depths = [item.get('depth', 0) for item in data if item.get('url')]
    avg_depth = np.mean(depths) if depths else 0
    if 0.3 <= in_centralization <= 0.6 and avg_depth > 2:
        topology_scores['hierarchical'] = 0.6 + (avg_depth / 10)

    # Flat: Low depth, uniform distribution
    if avg_depth < 2 and in_degree_std < avg_in_degree:
        topology_scores['flat'] = 0.7 + (2 - avg_depth) * 0.15

    # Determine detected topology
    detected_topology = max(topology_scores.items(), key=lambda x: x[1])
    topology_name = detected_topology[0]
    confidence = detected_topology[1]

    # Check if matches expected
    matches_expected = (expected_topology == topology_name) if expected_topology else None

    return {
        'detected_topology': topology_name,
        'confidence': round(confidence, 3),
        'matches_expected': matches_expected,
        'expected_topology': expected_topology,
        'topology_scores': {k: round(v, 3) for k, v in topology_scores.items()},
        'characteristics': {
            'hub_count': len(hubs),
            'avg_in_degree': round(avg_in_degree, 2),
            'avg_out_degree': round(avg_out_degree, 2),
            'in_centralization': round(in_centralization, 3),
            'out_centralization': round(out_centralization, 3),
            'avg_depth': round(avg_depth, 2)
        },
        'available': True
    }


def detect_architectural_antipatterns(data: List[Dict]) -> Dict:
    """
    Detect architectural antipatterns (orphan clusters, bottleneck pages).

    Identifies structural problems that indicate poor architecture or
    implementation issues.

    Args:
        data: List of URL dictionaries with links and parent_url

    Returns:
        Dictionary with detected antipatterns

    Example:
        {
            'antipatterns': {
                'orphan_clusters': [...],
                'bottleneck_pages': [...],
                'dead_end_clusters': [...],
                'circular_dependencies': [...]
            },
            'severity_score': 65  # 0-100, higher is worse
        }
    """
    if not data:
        return {
            'antipatterns': {},
            'severity_score': 0,
            'available': False
        }

    # Build graph
    graph = defaultdict(set)
    reverse_graph = defaultdict(set)
    all_urls = {item.get('url') for item in data if item.get('url')}

    for item in data:
        url = item.get('url', '')
        if not url:
            continue

        links = item.get('links', [])
        for link in links:
            if link in all_urls:
                graph[url].add(link)
                reverse_graph[link].add(url)

    antipatterns = {}

    # 1. Orphan clusters (pages with no incoming links)
    orphans = [url for url in all_urls if len(reverse_graph.get(url, set())) == 0]
    antipatterns['orphan_clusters'] = {
        'count': len(orphans),
        'percentage': (len(orphans) / len(all_urls)) * 100 if all_urls else 0,
        'examples': orphans[:10],
        'severity': 'high' if len(orphans) > len(all_urls) * 0.1 else 'medium' if len(orphans) > 0 else 'low'
    }

    # 2. Bottleneck pages (single point of failure - one inbound, many outbound)
    bottlenecks = []
    for url in all_urls:
        in_degree = len(reverse_graph.get(url, set()))
        out_degree = len(graph.get(url, set()))

        if in_degree == 1 and out_degree > 10:
            bottlenecks.append({
                'url': url,
                'in_degree': in_degree,
                'out_degree': out_degree,
                'risk_score': out_degree  # More outbound = higher risk
            })

    bottlenecks.sort(key=lambda x: x['risk_score'], reverse=True)

    antipatterns['bottleneck_pages'] = {
        'count': len(bottlenecks),
        'examples': bottlenecks[:10],
        'severity': 'high' if len(bottlenecks) > 5 else 'medium' if len(bottlenecks) > 0 else 'low'
    }

    # 3. Dead-end clusters (pages with no outbound links)
    dead_ends = [url for url in all_urls if len(graph.get(url, set())) == 0]
    antipatterns['dead_end_clusters'] = {
        'count': len(dead_ends),
        'percentage': (len(dead_ends) / len(all_urls)) * 100 if all_urls else 0,
        'examples': dead_ends[:10],
        'severity': 'medium' if len(dead_ends) > len(all_urls) * 0.2 else 'low'
    }

    # 4. Circular dependencies (A -> B -> A)
    circular_deps = _detect_circular_dependencies(graph)
    antipatterns['circular_dependencies'] = {
        'count': len(circular_deps),
        'examples': circular_deps[:10],
        'severity': 'low'  # Circular links are usually intentional
    }

    # 5. Hub overload (too many connections to single page)
    in_degrees = {url: len(reverse_graph.get(url, set())) for url in all_urls}
    max_in_degree = max(in_degrees.values()) if in_degrees else 0
    avg_in_degree = np.mean(list(in_degrees.values())) if in_degrees else 0

    overloaded_hubs = [
        {'url': url, 'in_degree': degree}
        for url, degree in in_degrees.items()
        if degree > avg_in_degree * 5  # 5x average
    ]

    antipatterns['overloaded_hubs'] = {
        'count': len(overloaded_hubs),
        'examples': sorted(overloaded_hubs, key=lambda x: x['in_degree'], reverse=True)[:10],
        'severity': 'medium' if len(overloaded_hubs) > 3 else 'low'
    }

    # Calculate overall severity score
    severity_weights = {
        'high': 30,
        'medium': 15,
        'low': 5
    }

    severity_score = sum(
        severity_weights[ap['severity']]
        for ap in antipatterns.values()
        if isinstance(ap, dict) and 'severity' in ap
    )

    return {
        'antipatterns': antipatterns,
        'severity_score': min(100, severity_score),
        'total_issues': sum(ap.get('count', 0) for ap in antipatterns.values() if isinstance(ap, dict)),
        'available': True
    }


def validate_breadcrumb_consistency(data: List[Dict]) -> Dict:
    """
    Validate breadcrumb consistency through path reconstruction.

    Ensures that URL paths form consistent hierarchies and that parent-child
    relationships make sense structurally.

    Args:
        data: List of URL dictionaries with parent_url

    Returns:
        Dictionary with breadcrumb validation results

    Example:
        {
            'consistency_score': 85.5,
            'inconsistencies': [
                {
                    'url': '...',
                    'parent_url': '...',
                    'issue': 'parent_deeper_than_child'
                }
            ]
        }
    """
    if not data:
        return {
            'consistency_score': 0,
            'available': False
        }

    inconsistencies = []
    total_relationships = 0

    for item in data:
        url = item.get('url', '')
        parent_url = item.get('parent_url')

        if not url or not parent_url or parent_url == url:
            continue

        total_relationships += 1

        # Parse URLs
        parsed_url = urlparse(url)
        parsed_parent = urlparse(parent_url)

        # Check 1: Parent should be on same domain
        if parsed_url.netloc != parsed_parent.netloc:
            inconsistencies.append({
                'url': url,
                'parent_url': parent_url,
                'issue': 'cross_domain_parent',
                'severity': 'high'
            })
            continue

        # Check 2: Parent should be shallower (fewer path segments)
        url_segments = [s for s in parsed_url.path.split('/') if s]
        parent_segments = [s for s in parsed_parent.path.split('/') if s]

        if len(parent_segments) >= len(url_segments):
            inconsistencies.append({
                'url': url,
                'parent_url': parent_url,
                'issue': 'parent_deeper_than_child',
                'severity': 'medium'
            })
            continue

        # Check 3: Parent path should be prefix of child path (for hierarchical structures)
        if len(parent_segments) > 0:
            # Check if parent path is prefix
            is_prefix = all(
                url_segments[i] == parent_segments[i]
                for i in range(min(len(parent_segments), len(url_segments)))
            )

            if not is_prefix:
                inconsistencies.append({
                    'url': url,
                    'parent_url': parent_url,
                    'issue': 'non_hierarchical_relationship',
                    'severity': 'low'
                })

    # Calculate consistency score
    if total_relationships == 0:
        consistency_score = 100
    else:
        # Weight by severity
        severity_weights = {'high': 1.0, 'medium': 0.5, 'low': 0.2}
        weighted_issues = sum(severity_weights[i['severity']] for i in inconsistencies)
        consistency_score = max(0, 100 - (weighted_issues / total_relationships) * 100)

    return {
        'consistency_score': round(consistency_score, 2),
        'total_relationships': total_relationships,
        'inconsistency_count': len(inconsistencies),
        'inconsistencies': inconsistencies[:20],  # Top 20
        'issues_by_severity': {
            'high': sum(1 for i in inconsistencies if i['severity'] == 'high'),
            'medium': sum(1 for i in inconsistencies if i['severity'] == 'medium'),
            'low': sum(1 for i in inconsistencies if i['severity'] == 'low')
        },
        'available': True
    }


def identify_dark_matter_urls(data: List[Dict]) -> Dict:
    """
    Identify "dark matter" URLs (high depth but no incoming links).

    These URLs are deep in the site structure but aren't linked to from
    discovered pages, suggesting poor internal linking or data quality issues.

    Args:
        data: List of URL dictionaries with depth and links

    Returns:
        Dictionary with dark matter URL analysis

    Example:
        {
            'dark_matter_urls': [
                {'url': '...', 'depth': 5, 'in_degree': 0}
            ],
            'dark_matter_percentage': 12.5
        }
    """
    if not data:
        return {
            'dark_matter_urls': [],
            'available': False
        }

    # Build reverse graph
    reverse_graph = defaultdict(set)
    all_urls = {item.get('url') for item in data if item.get('url')}

    for item in data:
        url = item.get('url', '')
        if not url:
            continue

        links = item.get('links', [])
        for link in links:
            if link in all_urls:
                reverse_graph[link].add(url)

    # Find dark matter URLs
    dark_matter = []
    depth_threshold = 3  # Consider URLs at depth 3+ as "deep"

    for item in data:
        url = item.get('url', '')
        depth = item.get('depth', 0)

        if not url:
            continue

        in_degree = len(reverse_graph.get(url, set()))

        # Dark matter: deep URL with no or few incoming links
        if depth >= depth_threshold and in_degree <= 1:
            dark_matter.append({
                'url': url,
                'depth': depth,
                'in_degree': in_degree,
                'dark_matter_score': depth * (2 - in_degree)  # Higher score = darker
            })

    # Sort by dark matter score
    dark_matter.sort(key=lambda x: x['dark_matter_score'], reverse=True)

    return {
        'dark_matter_urls': dark_matter,
        'dark_matter_count': len(dark_matter),
        'dark_matter_percentage': (len(dark_matter) / len(all_urls)) * 100 if all_urls else 0,
        'avg_dark_matter_depth': round(np.mean([dm['depth'] for dm in dark_matter]), 2) if dark_matter else 0,
        'severity': 'high' if len(dark_matter) > len(all_urls) * 0.15 else 'medium' if len(dark_matter) > len(all_urls) * 0.05 else 'low',
        'recommendations': _generate_dark_matter_recommendations(dark_matter, len(all_urls)),
        'available': True
    }


# Helper functions

def _detect_circular_dependencies(graph: Dict[str, Set[str]]) -> List[Dict]:
    """Detect circular dependencies in graph."""
    circular_deps = []

    for url, targets in graph.items():
        for target in targets:
            # Check if target links back to url
            if url in graph.get(target, set()):
                circular_deps.append({
                    'url1': url,
                    'url2': target,
                    'type': 'bidirectional'
                })

    return circular_deps


def _generate_dark_matter_recommendations(dark_matter: List[Dict], total_urls: int) -> List[str]:
    """Generate recommendations based on dark matter analysis."""
    recommendations = []

    if not dark_matter:
        return ['No dark matter URLs detected. Internal linking appears healthy.']

    percentage = (len(dark_matter) / total_urls) * 100 if total_urls > 0 else 0

    if percentage > 15:
        recommendations.append('CRITICAL: Over 15% of URLs are poorly linked. Review internal linking strategy.')

    if percentage > 5:
        recommendations.append('Improve internal linking to deep content.')
        recommendations.append('Consider adding sitemap or navigation improvements.')

    avg_depth = np.mean([dm['depth'] for dm in dark_matter]) if dark_matter else 0
    if avg_depth > 5:
        recommendations.append('Consider flattening site hierarchy - average dark matter depth is very high.')

    return recommendations
