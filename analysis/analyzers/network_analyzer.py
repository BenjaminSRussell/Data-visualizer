"""
Network Analysis - Link Relationships and Graph Metrics

Purpose: Analyze URL network as a graph, compute centrality metrics,
         identify clusters, and detect link patterns
"""

from collections import Counter, defaultdict
from typing import Dict, List
from urllib.parse import urlparse

# Use shared utilities to eliminate redundancy
from analysis.utils.url_utilities import (
    get_base_url,
    is_internal_link,
    parse_url_components,
    resolve_link,
)


class NetworkAnalyzer:
    """Analyze URL network using graph theory metrics."""

    def __init__(self):
        self.graph = defaultdict(set)  # map each url to its linked urls
        self.reverse_graph = defaultdict(set)  # map each url to linking sources
        self.url_data = {}

    def analyze(self, data: List[Dict]) -> Dict:
        """
        Perform comprehensive network analysis.

        Args:
            data: List of URL dictionaries from JSONL

        Returns:
            Network analysis results
        """
        self._build_network(data)

        results = {
            'network_metrics': self._compute_network_metrics(),
            'centrality': self._compute_centrality(),
            'clustering': self._analyze_clusters(),
            'link_patterns': self._analyze_link_patterns(),
            'domain_analysis': self._analyze_domains(),
            'authority_hub_analysis': self._compute_authority_hubs(),
            'community_detection': self._detect_communities(),
            'bottlenecks': self._find_bottlenecks()
        }

        return results

    def _build_network(self, data: List[Dict]):
        """Build network graph from URL data."""

        # first pass collects all urls
        all_urls = {item.get('url') for item in data if item.get('url')}

        for item in data:
            url = item.get('url', '')
            if not url:
                continue

            self.url_data[url] = item
            links = item.get('links', [])

            base_url = get_base_url(url)  # Use shared utility

            for link in links:
                # resolve relative links using shared utility
                target = resolve_link(link, url, base_url)

                if target and is_internal_link(url, target):  # Use shared utility
                    self.graph[url].add(target)
                    self.reverse_graph[target].add(url)

    def _compute_network_metrics(self) -> Dict:
        """Compute basic network metrics."""

        total_nodes = len(self.url_data)
        total_edges = sum(len(links) for links in self.graph.values())

        # calculate density as actual edges over possible edges
        possible_edges = total_nodes * (total_nodes - 1)
        density = (total_edges / possible_edges) if possible_edges > 0 else 0

        # compute degree distribution
        in_degrees = [len(self.reverse_graph.get(url, set())) for url in self.url_data]
        out_degrees = [len(self.graph.get(url, set())) for url in self.url_data]

        metrics = {
            'nodes': total_nodes,
            'edges': total_edges,
            'density': density,
            'average_degree': (sum(in_degrees) + sum(out_degrees)) / (2 * total_nodes) if total_nodes > 0 else 0,
            'average_in_degree': sum(in_degrees) / total_nodes if total_nodes > 0 else 0,
            'average_out_degree': sum(out_degrees) / total_nodes if total_nodes > 0 else 0,
            'max_in_degree': max(in_degrees) if in_degrees else 0,
            'max_out_degree': max(out_degrees) if out_degrees else 0,
            'reciprocity': self._calculate_reciprocity()
        }

        return metrics

    def _calculate_reciprocity(self) -> float:
        """Calculate reciprocity (bidirectional links)."""

        reciprocal_count = 0
        total_edges = 0

        for url, targets in self.graph.items():
            for target in targets:
                total_edges += 1
                if url in self.graph.get(target, set()):
                    reciprocal_count += 1

        return (reciprocal_count / total_edges) if total_edges > 0 else 0

    def _compute_centrality(self) -> Dict:
        """Compute centrality metrics for nodes."""

        # compute degree centrality
        degree_centrality = {}
        for url in self.url_data:
            in_degree = len(self.reverse_graph.get(url, set()))
            out_degree = len(self.graph.get(url, set()))
            degree_centrality[url] = in_degree + out_degree

        # select top nodes by degree centrality
        top_by_degree = sorted(
            degree_centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        # approximate betweenness using depth
        betweenness = {}
        for url, item in self.url_data.items():
            depth = item.get('depth', 0)
            # pages at mid-depth act as bridges
            betweenness[url] = 1 / (1 + abs(depth - 3))  # assume optimal depth is 3

        top_by_betweenness = sorted(
            betweenness.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        # compute in-degree centrality for authority
        in_centrality = {
            url: len(self.reverse_graph.get(url, set()))
            for url in self.url_data
        }

        top_by_in = sorted(
            in_centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        # compute out-degree centrality for hub scoring
        out_centrality = {
            url: len(self.graph.get(url, set()))
            for url in self.url_data
        }

        top_by_out = sorted(
            out_centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        return {
            'top_by_degree': [{'url': url, 'degree': degree} for url, degree in top_by_degree],
            'top_by_in_degree': [{'url': url, 'in_degree': degree} for url, degree in top_by_in],
            'top_by_out_degree': [{'url': url, 'out_degree': degree} for url, degree in top_by_out],
            'top_by_betweenness': [{'url': url, 'betweenness': score} for url, score in top_by_betweenness]
        }

    def _analyze_clusters(self) -> Dict:
        """Analyze clustering in the network."""

        # compute local clustering coefficient
        clustering_coefficients = {}

        for url in self.url_data:
            neighbors = self.graph.get(url, set())
            k = len(neighbors)

            if k < 2:
                clustering_coefficients[url] = 0
                continue

            # count edges between neighbors
            edges_between_neighbors = 0
            for n1 in neighbors:
                for n2 in neighbors:
                    if n1 != n2 and n2 in self.graph.get(n1, set()):
                        edges_between_neighbors += 1

            # derive clustering coefficient
            possible_edges = k * (k - 1)
            clustering_coefficients[url] = edges_between_neighbors / possible_edges if possible_edges > 0 else 0

        # compute global clustering coefficient
        global_clustering = sum(clustering_coefficients.values()) / len(clustering_coefficients) if clustering_coefficients else 0

        # rank highly clustered regions
        highly_clustered = sorted(
            clustering_coefficients.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        return {
            'global_clustering_coefficient': global_clustering,
            'highly_clustered_pages': [
                {'url': url, 'clustering_coefficient': coef}
                for url, coef in highly_clustered if coef > 0
            ]
        }

    def _analyze_link_patterns(self) -> Dict:
        """Analyze patterns in linking behavior."""

        patterns = {
            'self_links': 0,
            'cross_depth_links': defaultdict(int),
            'sibling_links': 0,
            'external_links': 0,
            'fragment_links': 0
        }

        for url, item in self.url_data.items():
            source_depth = item.get('depth', 0)
            links = item.get('links', [])

            for link in links:
                # track self links
                if link == url or link.startswith('#'):
                    patterns['self_links'] += 1
                    if link.startswith('#'):
                        patterns['fragment_links'] += 1
                    continue

                # resolve the candidate link using shared utility
                target = resolve_link(link, url, get_base_url(url))

                if not target:
                    continue

                # count external links using shared utility
                if not is_internal_link(url, target):
                    patterns['external_links'] += 1
                    continue

                # capture cross-depth relationships
                if target in self.url_data:
                    target_depth = self.url_data[target].get('depth', 0)
                    depth_diff = target_depth - source_depth

                    if depth_diff == 0:
                        patterns['sibling_links'] += 1
                    else:
                        patterns['cross_depth_links'][depth_diff] += 1

        return {
            'self_links': patterns['self_links'],
            'fragment_links': patterns['fragment_links'],
            'external_links': patterns['external_links'],
            'sibling_links': patterns['sibling_links'],
            'cross_depth_distribution': dict(patterns['cross_depth_links'])
        }

    def _analyze_domains(self) -> Dict:
        """Analyze domain diversity in links."""

        domain_counts = Counter()
        domain_links = defaultdict(set)

        for url, item in self.url_data.items():
            source_domain = urlparse(url).netloc
            links = item.get('links', [])

            for link in links:
                try:
                    if link.startswith('http'):
                        target_domain = urlparse(link).netloc
                        domain_counts[target_domain] += 1
                        domain_links[source_domain].add(target_domain)
                except:
                    continue

        return {
            'unique_domains_linked': len(domain_counts),
            'top_linked_domains': dict(domain_counts.most_common(20)),
            'domain_diversity_score': len(domain_counts) / len(self.url_data) if self.url_data else 0
        }

    def _compute_authority_hubs(self) -> Dict:
        """Compute HITS-like authority and hub scores."""

        # simplified hits algorithm with one iteration
        authority = {url: 1.0 for url in self.url_data}
        hub = {url: 1.0 for url in self.url_data}

        # update authority scores
        new_authority = {}
        for url in self.url_data:
            score = sum(hub.get(source, 0) for source in self.reverse_graph.get(url, set()))
            new_authority[url] = score

        # normalize authority vector
        max_auth = max(new_authority.values()) if new_authority.values() else 1
        authority = {url: score / max_auth for url, score in new_authority.items()}

        # update hub scores
        new_hub = {}
        for url in self.url_data:
            score = sum(authority.get(target, 0) for target in self.graph.get(url, set()))
            new_hub[url] = score

        # normalize hub vector
        max_hub = max(new_hub.values()) if new_hub.values() else 1
        hub = {url: score / max_hub for url, score in new_hub.items()}

        # extract top authorities and hubs
        top_authorities = sorted(authority.items(), key=lambda x: x[1], reverse=True)[:20]
        top_hubs = sorted(hub.items(), key=lambda x: x[1], reverse=True)[:20]

        return {
            'top_authorities': [{'url': url, 'authority_score': score} for url, score in top_authorities],
            'top_hubs': [{'url': url, 'hub_score': score} for url, score in top_hubs]
        }

    def _detect_communities(self) -> Dict:
        """Detect communities using simple path-based clustering."""

        communities = defaultdict(set)

        # group by url path prefix using shared utility
        for url in self.url_data:
            components = parse_url_components(url)
            path_parts = components['path_segments']

            # use first path segment as community identifier
            if path_parts:
                community_key = path_parts[0]
                communities[community_key].add(url)
            else:
                communities['root'].add(url)

        # sort communities by size
        sorted_communities = sorted(
            communities.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        return {
            'total_communities': len(communities),
            'top_communities': [
                {
                    'community': name,
                    'size': len(members),
                    'percentage': (len(members) / len(self.url_data)) * 100
                }
                for name, members in sorted_communities[:20]
            ]
        }

    def _find_bottlenecks(self) -> Dict:
        """Find potential bottleneck pages (single path pages)."""

        bottlenecks = []

        for url in self.url_data:
            in_degree = len(self.reverse_graph.get(url, set()))
            out_degree = len(self.graph.get(url, set()))

            # flag bottlenecks with one inbound link and many outbound
            if in_degree == 1 and out_degree > 5:
                bottlenecks.append({
                    'url': url,
                    'in_degree': in_degree,
                    'out_degree': out_degree
                })

        bottlenecks.sort(key=lambda x: x['out_degree'], reverse=True)

        return {
            'count': len(bottlenecks),
            'examples': bottlenecks[:20]
        }


def execute(data: List[Dict]) -> Dict:
    """
    Main execution function for network analysis.

    Args:
        data: List of URL dictionaries from JSONL

    Returns:
        Network analysis results
    """
    analyzer = NetworkAnalyzer()
    return analyzer.analyze(data)


def print_summary(results: Dict):
    """Print summary of network analysis."""

    print("Network analysis summary")

    metrics = results['network_metrics']
    print(f"Nodes: {metrics['nodes']:,}")
    print(f"Edges: {metrics['edges']:,}")
    print(f"Density: {metrics['density']:.6f}")
    print(f"Average Degree: {metrics['average_degree']:.2f}")

    centrality = results['centrality']
    if centrality['top_by_degree']:
        top = centrality['top_by_degree'][0]
        print(f"Most central page: {top['url'][:60]} (degree: {top['degree']})")

    communities = results['community_detection']
    print(f"Communities: {communities['total_communities']}")
    if communities['top_communities']:
        top_comm = communities['top_communities'][0]
        print(f"Largest: {top_comm['community']} ({top_comm['percentage']:.1f}%)")
