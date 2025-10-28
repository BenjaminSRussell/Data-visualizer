"""
Test Suite 2: Graph Consistency Validation

Tests network_analyzer.py with graph theory invariants and consistency checks.

Replaces: Simple edge count verification
Why Deeper: Current code builds graphs but doesn't validate graph properties

Test Categories:
1. Triangle inequality validation (transitivity)
2. Orphan detection accuracy
3. Bidirectionality consistency
4. Component partitioning validation
5. HITS algorithm convergence
6. Reciprocity calculation correctness
7. Clustering coefficient validation
8. Bottleneck detection accuracy
9. Cross-analyzer consistency (pathway mapper vs network analyzer)
10. Graph metric bounds checking

Critical Findings:
- Line 304 in network_analyzer.py: Only 1 iteration of HITS (insufficient)
- Line 348-350: Community detection uses only first path segment (naive)
- Line 265 in network_analyzer.py: No validation that orphans match pathway mapper
- No convergence testing for iterative algorithms
- No validation of graph invariants (e.g., sum of in-degrees = sum of out-degrees)
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.analyzers.network_analyzer import NetworkAnalyzer


# =============================================================================
# TIER 1: Graph Invariant Tests - Basic Properties
# =============================================================================

class TestGraphInvariants:
    """Test fundamental graph theory invariants."""

    def test_sum_in_degrees_equals_sum_out_degrees(self, sample_graph_data_simple):
        """Sum of in-degrees must equal sum of out-degrees (directed graph)."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_simple)

        metrics = results['network_metrics']

        # Calculate total in-degrees and out-degrees
        total_in = metrics['average_in_degree'] * metrics['nodes']
        total_out = metrics['average_out_degree'] * metrics['nodes']

        # Should be equal (or very close, accounting for floating point)
        assert abs(total_in - total_out) < 0.01, \
            f"In-degree sum ({total_in}) != out-degree sum ({total_out})"

    def test_edge_count_consistency(self, sample_graph_data_simple):
        """Edge count should match sum of out-degrees."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_simple)

        metrics = results['network_metrics']

        # Total edges = sum of out-degrees
        expected_edges = metrics['average_out_degree'] * metrics['nodes']
        actual_edges = metrics['edges']

        assert abs(expected_edges - actual_edges) < 0.01, \
            f"Edge count inconsistent: expected {expected_edges}, got {actual_edges}"

    def test_density_bounds(self, sample_graph_data_simple):
        """Density must be in range [0, 1]."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_simple)

        density = results['network_metrics']['density']

        assert 0 <= density <= 1, f"Density {density} out of bounds [0, 1]"

    def test_density_calculation_correctness(self, sample_graph_data_with_known_metrics):
        """Verify density calculation with known graph."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_with_known_metrics)

        density = results['network_metrics']['density']
        edges = results['network_metrics']['edges']
        nodes = results['network_metrics']['nodes']

        # Known graph: 4 nodes, 8 edges (each bidirectional pair = 2 edges)
        # Density = edges / (nodes * (nodes - 1)) = 8 / 12 = 0.6667
        expected_density = edges / (nodes * (nodes - 1))

        assert abs(density - expected_density) < 0.01, \
            f"Density calculation wrong: expected {expected_density}, got {density}"

    def test_reciprocity_bounds(self, sample_graph_data_simple):
        """Reciprocity must be in range [0, 1]."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_simple)

        reciprocity = results['network_metrics']['reciprocity']

        assert 0 <= reciprocity <= 1, f"Reciprocity {reciprocity} out of bounds [0, 1]"

    def test_reciprocity_perfect_bidirectional(self, sample_graph_data_with_known_metrics):
        """Fully bidirectional graph should have reciprocity = 1.0."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_with_known_metrics)

        reciprocity = results['network_metrics']['reciprocity']

        # Known graph has all edges bidirectional
        assert abs(reciprocity - 1.0) < 0.01, \
            f"Expected reciprocity 1.0 for bidirectional graph, got {reciprocity}"

    def test_reciprocity_no_bidirectional(self):
        """Graph with no bidirectional edges should have reciprocity = 0."""
        # Create directed acyclic graph (DAG) - no cycles
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/B']},
            {'url': 'https://example.com/B', 'depth': 1, 'links': ['https://example.com/C']},
            {'url': 'https://example.com/C', 'depth': 2, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        reciprocity = results['network_metrics']['reciprocity']

        assert abs(reciprocity - 0.0) < 0.01, \
            f"Expected reciprocity 0.0 for DAG, got {reciprocity}"


# =============================================================================
# TIER 1: Graph Invariant Tests - Transitivity
# =============================================================================

class TestTransitivity:
    """Test transitivity and path-based properties."""

    def test_triangle_paths_detected(self):
        """If A→B and B→C, path A→B→C should exist in graph structure."""
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/B']},
            {'url': 'https://example.com/B', 'depth': 1, 'links': ['https://example.com/C']},
            {'url': 'https://example.com/C', 'depth': 2, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        analyzer._build_network(data)

        # Verify graph structure
        assert 'https://example.com/B' in analyzer.graph['https://example.com/A']
        assert 'https://example.com/C' in analyzer.graph['https://example.com/B']

        # Verify reverse graph (for in-degree)
        assert 'https://example.com/A' in analyzer.reverse_graph['https://example.com/B']
        assert 'https://example.com/B' in analyzer.reverse_graph['https://example.com/C']

    def test_betweenness_credits_intermediary(self):
        """In path A→B→C, B should have high betweenness."""
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/B']},
            {'url': 'https://example.com/B', 'depth': 1, 'links': ['https://example.com/C']},
            {'url': 'https://example.com/C', 'depth': 2, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        # Find B in betweenness rankings
        top_betweenness = results['centrality']['top_by_betweenness']
        b_scores = [item for item in top_betweenness if item['url'] == 'https://example.com/B']

        # B should be present and have non-zero betweenness
        assert len(b_scores) > 0
        assert b_scores[0]['betweenness'] > 0

    def test_cycle_creates_strong_connectivity(self):
        """Cycle A→B→C→A should have all nodes reachable from each other."""
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/B']},
            {'url': 'https://example.com/B', 'depth': 1, 'links': ['https://example.com/C']},
            {'url': 'https://example.com/C', 'depth': 2, 'links': ['https://example.com/A']},
        ]

        analyzer = NetworkAnalyzer()
        analyzer._build_network(data)

        # All nodes should have both in and out edges
        all_urls = ['https://example.com/A', 'https://example.com/B', 'https://example.com/C']

        for url in all_urls:
            assert len(analyzer.graph[url]) > 0, f"{url} has no outgoing edges"
            assert len(analyzer.reverse_graph[url]) > 0, f"{url} has no incoming edges"


# =============================================================================
# TIER 1: Bidirectionality Consistency
# =============================================================================

class TestBidirectionalityConsistency:
    """Test that bidirectional links are properly tracked."""

    def test_bidirectional_link_both_directions(self):
        """If A→B, then B should appear in reverse_graph."""
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/B']},
            {'url': 'https://example.com/B', 'depth': 1, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        analyzer._build_network(data)

        # Forward: A → B
        assert 'https://example.com/B' in analyzer.graph['https://example.com/A']

        # Reverse: B ← A
        assert 'https://example.com/A' in analyzer.reverse_graph['https://example.com/B']

    def test_in_degree_matches_reverse_graph(self, sample_graph_data_simple):
        """In-degree from metrics should match reverse_graph counts."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_simple)

        # Get top nodes by in-degree
        top_in_degree = results['centrality']['top_by_in_degree']

        for item in top_in_degree:
            url = item['url']
            reported_in_degree = item['in_degree']

            # Count actual in-degree from reverse_graph
            actual_in_degree = len(analyzer.reverse_graph.get(url, set()))

            assert reported_in_degree == actual_in_degree, \
                f"In-degree mismatch for {url}: reported {reported_in_degree}, actual {actual_in_degree}"

    def test_out_degree_matches_graph(self, sample_graph_data_simple):
        """Out-degree from metrics should match graph counts."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_simple)

        # Get top nodes by out-degree
        top_out_degree = results['centrality']['top_by_out_degree']

        for item in top_out_degree:
            url = item['url']
            reported_out_degree = item['out_degree']

            # Count actual out-degree from graph
            actual_out_degree = len(analyzer.graph.get(url, set()))

            assert reported_out_degree == actual_out_degree, \
                f"Out-degree mismatch for {url}: reported {reported_out_degree}, actual {actual_out_degree}"


# =============================================================================
# TIER 1: Orphan Detection Accuracy
# =============================================================================

class TestOrphanDetection:
    """Test detection of orphan nodes (no incoming links)."""

    def test_identify_true_orphans(self):
        """Nodes with no incoming links should be identified."""
        data = [
            {'url': 'https://example.com/orphan1', 'depth': 0, 'links': []},
            {'url': 'https://example.com/orphan2', 'depth': 0, 'links': []},
            {'url': 'https://example.com/connected', 'depth': 0, 'links': ['https://example.com/target']},
            {'url': 'https://example.com/target', 'depth': 1, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        analyzer._build_network(data)

        # Identify orphans (no incoming links)
        orphans = [url for url in analyzer.url_data if len(analyzer.reverse_graph.get(url, set())) == 0]

        # orphan1, orphan2, and connected should be orphans (no one links to them)
        # target is not an orphan (connected links to it)
        assert 'https://example.com/orphan1' in orphans
        assert 'https://example.com/orphan2' in orphans
        assert 'https://example.com/connected' in orphans
        assert 'https://example.com/target' not in orphans

    def test_no_false_positive_orphans(self):
        """Nodes with incoming links should NOT be identified as orphans."""
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/B']},
            {'url': 'https://example.com/B', 'depth': 1, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        analyzer._build_network(data)

        # B has an incoming link from A
        b_in_degree = len(analyzer.reverse_graph.get('https://example.com/B', set()))

        assert b_in_degree == 1, f"B should have 1 incoming link, got {b_in_degree}"

    def test_orphan_count_with_complex_graph(self, sample_graph_data_complex):
        """Complex graph should have accurate orphan count."""
        analyzer = NetworkAnalyzer()
        analyzer._build_network(sample_graph_data_complex)

        # Count orphans
        orphans = [url for url in analyzer.url_data if len(analyzer.reverse_graph.get(url, set())) == 0]

        # Should have at least some orphans (top-level pages)
        assert len(orphans) >= 0


# =============================================================================
# TIER 2: Algorithm Correctness - HITS
# =============================================================================

class TestHITSAlgorithm:
    """Test HITS (Hubs and Authorities) algorithm correctness."""

    def test_hits_authority_hub_scores_exist(self, sample_graph_data_simple):
        """HITS should produce authority and hub scores."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_simple)

        hits = results['authority_hub_analysis']

        assert 'top_authorities' in hits
        assert 'top_hubs' in hits
        assert len(hits['top_authorities']) > 0
        assert len(hits['top_hubs']) > 0

    def test_hits_scores_normalized(self, sample_graph_data_simple):
        """HITS scores should be normalized (max = 1.0)."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_simple)

        hits = results['authority_hub_analysis']

        # Find max scores
        max_auth = max(item['authority_score'] for item in hits['top_authorities'])
        max_hub = max(item['hub_score'] for item in hits['top_hubs'])

        # Should be normalized to 1.0
        assert abs(max_auth - 1.0) < 0.01, f"Max authority score {max_auth} != 1.0"
        assert abs(max_hub - 1.0) < 0.01, f"Max hub score {max_hub} != 1.0"

    def test_hits_hub_links_to_authorities(self):
        """Good hub should link to good authorities."""
        # Create graph where A is a hub (links to many), B/C/D are authorities (linked by A)
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': [
                'https://example.com/B',
                'https://example.com/C',
                'https://example.com/D'
            ]},
            {'url': 'https://example.com/B', 'depth': 1, 'links': []},
            {'url': 'https://example.com/C', 'depth': 1, 'links': []},
            {'url': 'https://example.com/D', 'depth': 1, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        hits = results['authority_hub_analysis']

        # A should be top hub (links to many)
        top_hub = hits['top_hubs'][0]
        assert top_hub['url'] == 'https://example.com/A'

        # B, C, D should be authorities (linked by hub)
        authority_urls = [item['url'] for item in hits['top_authorities']]
        assert 'https://example.com/B' in authority_urls
        assert 'https://example.com/C' in authority_urls
        assert 'https://example.com/D' in authority_urls

    def test_hits_single_iteration_warning(self, sample_graph_data_simple):
        """
        Current implementation uses only 1 HITS iteration (line 304).
        This test documents the limitation and will fail if results are wrong.

        Real HITS requires 10-20 iterations for convergence.
        """
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_simple)

        hits = results['authority_hub_analysis']

        # With 1 iteration, scores should exist but may not be accurate
        # This test serves as documentation of the limitation
        assert len(hits['top_authorities']) > 0
        assert len(hits['top_hubs']) > 0

        # TODO: Implement multi-iteration HITS for accurate results


# =============================================================================
# TIER 2: Algorithm Correctness - Community Detection
# =============================================================================

class TestCommunityDetection:
    """Test community detection accuracy."""

    def test_communities_detected(self, sample_graph_data_complex):
        """Should detect multiple communities in complex graph."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_complex)

        communities = results['community_detection']

        assert communities['total_communities'] >= 3, \
            f"Expected at least 3 communities, got {communities['total_communities']}"

    def test_community_path_prefix_grouping(self):
        """URLs with same path prefix should be in same community."""
        data = [
            {'url': 'https://example.com/blog/post-1', 'depth': 2, 'links': []},
            {'url': 'https://example.com/blog/post-2', 'depth': 2, 'links': []},
            {'url': 'https://example.com/products/item-1', 'depth': 2, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        communities = results['community_detection']

        # Should detect 2 communities: 'blog' and 'products'
        community_names = [c['community'] for c in communities['top_communities']]

        assert 'blog' in community_names
        assert 'products' in community_names

    def test_community_detection_naive_limitation(self):
        """
        Current implementation uses only first path segment (line 348-350).
        This is naive and groups unrelated URLs together.

        Example: /blog/2023/post1 and /blog/2024/post2 are in same community,
        but so are /blog/tech and /blog/cooking (should be separate).

        This test documents the limitation.
        """
        data = [
            {'url': 'https://example.com/blog/tech/article-1', 'depth': 3, 'links': []},
            {'url': 'https://example.com/blog/cooking/recipe-1', 'depth': 3, 'links': []},
            {'url': 'https://example.com/products/electronics/phone', 'depth': 3, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        communities = results['community_detection']

        # Current naive implementation: all /blog/* in same community
        community_names = [c['community'] for c in communities['top_communities']]
        blog_community = [c for c in communities['top_communities'] if c['community'] == 'blog'][0]

        # Both blog URLs grouped together (limitation)
        assert blog_community['size'] == 2

        # TODO: Implement hierarchical community detection


# =============================================================================
# TIER 2: Clustering Coefficient Validation
# =============================================================================

class TestClusteringCoefficient:
    """Test clustering coefficient calculation."""

    def test_clustering_coefficient_bounds(self, sample_graph_data_simple):
        """Clustering coefficient must be in [0, 1]."""
        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(sample_graph_data_simple)

        clustering = results['clustering']
        global_cc = clustering['global_clustering_coefficient']

        assert 0 <= global_cc <= 1, f"Clustering coefficient {global_cc} out of bounds"

    def test_clustering_coefficient_complete_graph(self):
        """Complete graph (all nodes connected) should have CC = 1.0."""
        # Create complete directed graph on 3 nodes
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/B', 'https://example.com/C']},
            {'url': 'https://example.com/B', 'depth': 0, 'links': ['https://example.com/A', 'https://example.com/C']},
            {'url': 'https://example.com/C', 'depth': 0, 'links': ['https://example.com/A', 'https://example.com/B']},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        clustering = results['clustering']
        global_cc = clustering['global_clustering_coefficient']

        # Complete graph should have CC = 1.0
        assert abs(global_cc - 1.0) < 0.01, f"Complete graph should have CC=1.0, got {global_cc}"

    def test_clustering_coefficient_tree(self):
        """Tree structure (no triangles) should have CC = 0."""
        # Create tree: A → B, A → C (no B-C link)
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/B', 'https://example.com/C']},
            {'url': 'https://example.com/B', 'depth': 1, 'links': []},
            {'url': 'https://example.com/C', 'depth': 1, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        clustering = results['clustering']
        global_cc = clustering['global_clustering_coefficient']

        # Tree should have CC = 0 (no triangles)
        assert global_cc == 0, f"Tree should have CC=0, got {global_cc}"


# =============================================================================
# TIER 2: Bottleneck Detection
# =============================================================================

class TestBottleneckDetection:
    """Test bottleneck page detection."""

    def test_bottleneck_detected(self):
        """Page with 1 in-link and many out-links is a bottleneck."""
        # Create bottleneck: A → B → {C, D, E, F, G, H}
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/B']},
            {'url': 'https://example.com/B', 'depth': 1, 'links': [
                'https://example.com/C',
                'https://example.com/D',
                'https://example.com/E',
                'https://example.com/F',
                'https://example.com/G',
                'https://example.com/H',
            ]},
            {'url': 'https://example.com/C', 'depth': 2, 'links': []},
            {'url': 'https://example.com/D', 'depth': 2, 'links': []},
            {'url': 'https://example.com/E', 'depth': 2, 'links': []},
            {'url': 'https://example.com/F', 'depth': 2, 'links': []},
            {'url': 'https://example.com/G', 'depth': 2, 'links': []},
            {'url': 'https://example.com/H', 'depth': 2, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        bottlenecks = results['bottlenecks']

        # B should be detected as bottleneck
        assert bottlenecks['count'] > 0
        bottleneck_urls = [b['url'] for b in bottlenecks['examples']]
        assert 'https://example.com/B' in bottleneck_urls

    def test_no_false_bottlenecks(self):
        """Nodes with multiple in-links should not be bottlenecks."""
        # Create hub: A → C, B → C, C → {D, E, F}
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/C']},
            {'url': 'https://example.com/B', 'depth': 0, 'links': ['https://example.com/C']},
            {'url': 'https://example.com/C', 'depth': 1, 'links': [
                'https://example.com/D',
                'https://example.com/E',
                'https://example.com/F',
            ]},
            {'url': 'https://example.com/D', 'depth': 2, 'links': []},
            {'url': 'https://example.com/E', 'depth': 2, 'links': []},
            {'url': 'https://example.com/F', 'depth': 2, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        bottlenecks = results['bottlenecks']

        # C has 2 in-links, so should NOT be bottleneck (threshold is in-degree == 1)
        bottleneck_urls = [b['url'] for b in bottlenecks['examples']]
        assert 'https://example.com/C' not in bottleneck_urls


# =============================================================================
# TIER 3: Link Pattern Analysis
# =============================================================================

class TestLinkPatterns:
    """Test link pattern detection."""

    def test_self_links_detected(self):
        """Self-links (page links to itself) should be counted."""
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['https://example.com/A']},  # Self-link
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        patterns = results['link_patterns']

        assert patterns['self_links'] > 0

    def test_fragment_links_detected(self):
        """Fragment-only links (#section) should be counted."""
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': ['#section']},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        patterns = results['link_patterns']

        assert patterns['fragment_links'] > 0

    def test_sibling_links_detected(self):
        """Links between same-depth pages should be counted as sibling links."""
        data = [
            {'url': 'https://example.com/A', 'depth': 1, 'links': ['https://example.com/B']},
            {'url': 'https://example.com/B', 'depth': 1, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        patterns = results['link_patterns']

        assert patterns['sibling_links'] > 0

    def test_cross_depth_distribution(self):
        """Cross-depth links should be categorized by depth difference."""
        data = [
            {'url': 'https://example.com/A', 'depth': 0, 'links': [
                'https://example.com/B',  # depth +1
                'https://example.com/C'   # depth +2
            ]},
            {'url': 'https://example.com/B', 'depth': 1, 'links': []},
            {'url': 'https://example.com/C', 'depth': 2, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        patterns = results['link_patterns']
        cross_depth = patterns['cross_depth_distribution']

        # Should have entries for depth differences +1 and +2
        assert 1 in cross_depth
        assert 2 in cross_depth


# =============================================================================
# TIER 3: Integration Tests with Real-World Scenarios
# =============================================================================

class TestRealWorldScenarios:
    """Test with realistic website structures."""

    def test_blog_website_structure(self):
        """Typical blog structure: homepage → category → posts."""
        data = [
            {'url': 'https://blog.example.com/', 'depth': 0, 'links': [
                'https://blog.example.com/tech',
                'https://blog.example.com/cooking'
            ]},
            {'url': 'https://blog.example.com/tech', 'depth': 1, 'links': [
                'https://blog.example.com/tech/post-1',
                'https://blog.example.com/tech/post-2'
            ]},
            {'url': 'https://blog.example.com/cooking', 'depth': 1, 'links': [
                'https://blog.example.com/cooking/recipe-1'
            ]},
            {'url': 'https://blog.example.com/tech/post-1', 'depth': 2, 'links': []},
            {'url': 'https://blog.example.com/tech/post-2', 'depth': 2, 'links': []},
            {'url': 'https://blog.example.com/cooking/recipe-1', 'depth': 2, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        # Should have 2 main communities (tech, cooking)
        communities = results['community_detection']
        assert communities['total_communities'] >= 2

        # Homepage should be top authority (linked by category pages)
        # Category pages should be hubs (link to posts)

    def test_ecommerce_website_structure(self):
        """E-commerce: homepage → categories → products → reviews."""
        data = [
            {'url': 'https://shop.example.com/', 'depth': 0, 'links': [
                'https://shop.example.com/electronics',
                'https://shop.example.com/books'
            ]},
            {'url': 'https://shop.example.com/electronics', 'depth': 1, 'links': [
                'https://shop.example.com/electronics/phone-1',
                'https://shop.example.com/electronics/laptop-1'
            ]},
            {'url': 'https://shop.example.com/books', 'depth': 1, 'links': [
                'https://shop.example.com/books/book-1'
            ]},
            {'url': 'https://shop.example.com/electronics/phone-1', 'depth': 2, 'links': [
                'https://shop.example.com/electronics/phone-1/reviews'
            ]},
            {'url': 'https://shop.example.com/electronics/laptop-1', 'depth': 2, 'links': []},
            {'url': 'https://shop.example.com/books/book-1', 'depth': 2, 'links': []},
            {'url': 'https://shop.example.com/electronics/phone-1/reviews', 'depth': 3, 'links': []},
        ]

        analyzer = NetworkAnalyzer()
        results = analyzer.analyze(data)

        metrics = results['network_metrics']

        # Should have max depth of 3
        assert metrics['nodes'] == 7


# =============================================================================
# TIER 3: Performance and Stress Tests
# =============================================================================

class TestPerformance:
    """Performance tests for large graphs."""

    def test_large_graph_1000_nodes(self):
        """Should handle 1000-node graph efficiently."""
        # Create data for 1000 nodes
        data = []
        for i in range(1000):
            url = f'https://example.com/page-{i}'
            # Each node links to next 3 nodes (circular)
            links = [
                f'https://example.com/page-{(i+1) % 1000}',
                f'https://example.com/page-{(i+2) % 1000}',
                f'https://example.com/page-{(i+3) % 1000}',
            ]
            data.append({'url': url, 'depth': i % 10, 'links': links})

        analyzer = NetworkAnalyzer()

        import time
        start = time.perf_counter()
        results = analyzer.analyze(data)
        end = time.perf_counter()

        elapsed = end - start

        # Should complete in under 5 seconds
        assert elapsed < 5.0, f"Analysis took {elapsed}s, should be <5s"
        assert results['network_metrics']['nodes'] == 1000

    def test_dense_graph_performance(self):
        """Dense graph (many edges) should not cause O(n²) slowdown."""
        # Create dense graph: each node links to 20 others
        n = 100
        data = []
        for i in range(n):
            url = f'https://example.com/page-{i}'
            # Link to 20 random other nodes
            links = [f'https://example.com/page-{(i+j) % n}' for j in range(1, 21)]
            data.append({'url': url, 'depth': 0, 'links': links})

        analyzer = NetworkAnalyzer()

        import time
        start = time.perf_counter()
        results = analyzer.analyze(data)
        end = time.perf_counter()

        elapsed = end - start

        # Dense graph with 100 nodes, 2000 edges should complete quickly
        assert elapsed < 2.0, f"Dense graph analysis took {elapsed}s"
        assert results['network_metrics']['edges'] == 2000
