"""
Pathway Mapper - Navigation Flow and Site Architecture Analysis

Purpose: Map user navigation flows, identify entry points, analyze site
         architecture, and discover navigation patterns
"""

from collections import defaultdict, deque
from typing import Dict, List, Set

from analysis.utils.general_metrics import analyze_depth_flow, get_max_depth

# Use shared utilities to eliminate redundancy
from analysis.utils.url_utilities import (
    get_base_url,
    is_same_domain,
    parse_url_components,
    resolve_link,
)


class PathwayMapper:
    """Map navigation pathways and site architecture."""

    def __init__(self):
        self.url_to_data = {}
        self.parent_child_map = defaultdict(list)
        self.child_parent_map = {}
        self.url_graph = defaultdict(set)
        self.entry_points = []
        self.dead_ends = []
        self.hub_pages = []

    def analyze(self, data: List[Dict]) -> Dict:
        """
        Analyze navigation pathways and site architecture.

        Args:
            data: List of URL dictionaries from JSONL

        Returns:
            Pathway analysis results
        """
        self._build_graph(data)

        results = {
            'architecture': self._analyze_architecture(),
            'entry_points': self._find_entry_points(),
            'navigation_hubs': self._find_navigation_hubs(),
            'dead_ends': self._find_dead_ends(),
            'pathways': self._extract_common_pathways(),
            'depth_flow': self._analyze_depth_flow(),
            'connectivity': self._analyze_connectivity(),
            'breadcrumb_analysis': self._analyze_breadcrumbs(),
            'page_importance': self._calculate_page_importance()
        }

        return results

    def _build_graph(self, data: List[Dict]):
        """Build URL relationship graph."""

        for item in data:
            url = item.get('url', '')
            self.url_to_data[url] = item

            # record parent-child relationships
            parent = item.get('parent_url')
            if parent and parent != url:
                self.parent_child_map[parent].append(url)
                self.child_parent_map[url] = parent

            # populate link graph
            links = item.get('links', [])
            base_url = get_base_url(url)  # Use shared utility

            for link in links:
                # resolve relative links using shared utility
                resolved_link = resolve_link(link, url, base_url)

                if resolved_link and is_same_domain(url, resolved_link):
                    self.url_graph[url].add(resolved_link)

    def _analyze_architecture(self) -> Dict:
        """Analyze overall site architecture."""

        # Use shared utility for max_depth calculation
        data_list = list(self.url_to_data.values())
        max_depth_value = get_max_depth(data_list)

        architecture = {
            'total_pages': len(self.url_to_data),
            'total_relationships': sum(len(children) for children in self.parent_child_map.values()),
            'max_depth': max_depth_value,
            'avg_children_per_parent': 0,
            'orphan_pages': 0,
            'architecture_type': 'unknown'
        }

        # calculate average children per parent
        if self.parent_child_map:
            architecture['avg_children_per_parent'] = (
                sum(len(children) for children in self.parent_child_map.values()) /
                len(self.parent_child_map)
            )

        # find orphan pages without parents
        orphans = [url for url in self.url_to_data if url not in self.child_parent_map and url not in self.parent_child_map]
        architecture['orphan_pages'] = len(orphans)

        # determine architecture type
        architecture['architecture_type'] = self._classify_architecture(architecture)

        return architecture

    def _classify_architecture(self, arch: Dict) -> str:
        """Classify site architecture type."""
        max_depth = arch['max_depth']
        avg_children = arch['avg_children_per_parent']

        if max_depth <= 3 and avg_children > 10:
            return 'flat'
        elif max_depth > 5 and avg_children < 5:
            return 'deep'
        elif avg_children > 7:
            return 'wide'
        else:
            return 'balanced'

    def _find_entry_points(self) -> Dict:
        """Find potential entry points (low depth, high importance)."""

        entry_points = []

        for url, item in self.url_to_data.items():
            depth = item.get('depth', 0)

            # treat depth 0-2 pages as entry candidates
            if depth <= 2:
                entry_points.append({
                    'url': url,
                    'depth': depth,
                    'children_count': len(self.parent_child_map.get(url, [])),
                    'links_count': len(self.url_graph.get(url, set()))
                })

        # sort entry points by combined child and link counts
        entry_points.sort(
            key=lambda x: x['children_count'] + x['links_count'],
            reverse=True
        )

        return {
            'count': len(entry_points),
            'top_entry_points': entry_points[:20]
        }

    def _find_navigation_hubs(self) -> Dict:
        """Find navigation hub pages (high connectivity)."""

        hubs = []

        for url, item in self.url_to_data.items():
            # count outbound links
            outbound = len(self.url_graph.get(url, set()))

            # count inbound links
            inbound = sum(1 for links in self.url_graph.values() if url in links)

            # qualify hubs by high outbound reach
            if outbound > 20 or inbound > 10:
                hubs.append({
                    'url': url,
                    'outbound_links': outbound,
                    'inbound_links': inbound,
                    'total_connectivity': outbound + inbound,
                    'depth': item.get('depth', 0)
                })

        hubs.sort(key=lambda x: x['total_connectivity'], reverse=True)

        return {
            'count': len(hubs),
            'top_hubs': hubs[:20]
        }

    def _find_dead_ends(self) -> Dict:
        """Find dead-end pages (no outbound links)."""

        dead_ends = []

        for url, item in self.url_to_data.items():
            outbound = len(self.url_graph.get(url, set()))

            if outbound == 0:
                dead_ends.append({
                    'url': url,
                    'depth': item.get('depth', 0),
                    'has_parent': url in self.child_parent_map
                })

        return {
            'count': len(dead_ends),
            'percentage': (len(dead_ends) / len(self.url_to_data)) * 100 if self.url_to_data else 0,
            'examples': dead_ends[:20]
        }

    def _extract_common_pathways(self) -> Dict:
        """Extract common navigation pathways."""

        pathways = defaultdict(int)

        # trace pathways from each url back to root
        for url in self.url_to_data:
            pathway = self._trace_pathway(url)
            if pathway:
                pathway_str = ' -> '.join(self._simplify_urls(pathway))
                pathways[pathway_str] += 1

        # rank top pathways
        sorted_pathways = sorted(
            pathways.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            'total_unique_pathways': len(pathways),
            'top_pathways': [
                {'pathway': path, 'frequency': count}
                for path, count in sorted_pathways[:30]
            ]
        }

    def _trace_pathway(self, url: str, max_depth: int = 10) -> List[str]:
        """Trace pathway from URL back to root."""

        pathway = [url]
        current = url
        depth = 0

        while current in self.child_parent_map and depth < max_depth:
            parent = self.child_parent_map[current]
            if parent in pathway:  # prevent pathway cycles
                break
            pathway.insert(0, parent)
            current = parent
            depth += 1

        return pathway

    def _simplify_urls(self, urls: List[str]) -> List[str]:
        """Simplify URLs to readable path segments."""

        simplified = []
        for url in urls:
            # Use shared utility for parsing
            components = parse_url_components(url)
            path = components['path'].strip('/')

            # use last segment or fallback to root
            if path:
                segments = path.split('/')
                # prefer last two segments when available
                if len(segments) >= 2:
                    simplified.append('/'.join(segments[-2:]))
                else:
                    simplified.append(segments[-1])
            else:
                simplified.append('root')

        return simplified

    def _analyze_depth_flow(self) -> Dict:
        """Analyze how content flows across depth levels."""
        # Use shared utility for depth flow analysis (eliminates redundancy)
        data_list = list(self.url_to_data.values())
        depth_flow_metrics = analyze_depth_flow(data_list)

        # Add link count information which is specific to pathway mapper
        for url, item in self.url_to_data.items():
            depth = item.get('depth', 0)
            if depth in depth_flow_metrics:
                # Add average links if not already present
                if 'avg_links' not in depth_flow_metrics[depth]:
                    depth_flow_metrics[depth]['avg_links'] = 0
                    depth_flow_metrics[depth]['total_links'] = 0

        # Calculate link metrics per depth
        link_counts = defaultdict(list)
        for url, item in self.url_to_data.items():
            depth = item.get('depth', 0)
            links_count = len(self.url_graph.get(url, set()))
            link_counts[depth].append(links_count)

        # Add link averages to metrics
        for depth, links in link_counts.items():
            if depth in depth_flow_metrics:
                depth_flow_metrics[depth]['avg_links'] = sum(links) / len(links) if links else 0

        return depth_flow_metrics

    def _analyze_connectivity(self) -> Dict:
        """Analyze overall connectivity of the site."""

        total_urls = len(self.url_to_data)

        # count connected components via bfs
        visited = set()
        components = []

        for start_url in self.url_to_data:
            if start_url not in visited:
                component = self._bfs_component(start_url, visited)
                components.append(component)

        # derive connectivity metrics
        largest_component = max(len(comp) for comp in components) if components else 0

        connectivity = {
            'total_components': len(components),
            'largest_component_size': largest_component,
            'largest_component_percentage': (largest_component / total_urls) * 100 if total_urls > 0 else 0,
            'is_fully_connected': len(components) == 1,
            'isolated_pages': sum(1 for comp in components if len(comp) == 1)
        }

        return connectivity

    def _bfs_component(self, start_url: str, visited: Set[str]) -> List[str]:
        """Find connected component using BFS."""

        component = []
        queue = deque([start_url])
        visited.add(start_url)

        while queue:
            url = queue.popleft()
            component.append(url)

            # traverse child relations
            for child in self.parent_child_map.get(url, []):
                if child not in visited:
                    visited.add(child)
                    queue.append(child)

            # traverse parent relation
            if url in self.child_parent_map:
                parent = self.child_parent_map[url]
                if parent not in visited:
                    visited.add(parent)
                    queue.append(parent)

            # traverse link relations
            for linked in self.url_graph.get(url, set()):
                if linked not in visited and linked in self.url_to_data:
                    visited.add(linked)
                    queue.append(linked)

        return component

    def _analyze_breadcrumbs(self) -> Dict:
        """Analyze breadcrumb structure quality."""

        breadcrumb_quality = {
            'clear_hierarchy': 0,
            'unclear_hierarchy': 0,
            'avg_breadcrumb_length': 0
        }

        total_length = 0

        for url, item in self.url_to_data.items():
            pathway = self._trace_pathway(url)
            total_length += len(pathway)

            # treat consistent depth as clear hierarchy
            expected_depth = len(pathway) - 1
            actual_depth = item.get('depth', 0)

            if expected_depth == actual_depth:
                breadcrumb_quality['clear_hierarchy'] += 1
            else:
                breadcrumb_quality['unclear_hierarchy'] += 1

        breadcrumb_quality['avg_breadcrumb_length'] = (
            total_length / len(self.url_to_data) if self.url_to_data else 0
        )

        breadcrumb_quality['hierarchy_clarity_percentage'] = (
            (breadcrumb_quality['clear_hierarchy'] / len(self.url_to_data)) * 100
            if self.url_to_data else 0
        )

        return breadcrumb_quality

    def _calculate_page_importance(self) -> Dict:
        """Calculate page importance using PageRank-like algorithm."""

        # build composite importance score
        importance_scores = []

        for url, item in self.url_to_data.items():
            score = 0

            # factor 1 rewards shallow depth
            depth = item.get('depth', 0)
            score += max(0, 10 - depth) * 10

            # factor 2 rewards outbound reach
            outbound = len(self.url_graph.get(url, set()))
            score += min(outbound, 50) * 2

            # factor 3 rewards inbound demand
            inbound = sum(1 for links in self.url_graph.values() if url in links)
            score += min(inbound, 20) * 5

            # factor 4 rewards child coverage
            children = len(self.parent_child_map.get(url, []))
            score += min(children, 30) * 3

            importance_scores.append({
                'url': url,
                'importance_score': score,
                'depth': depth,
                'inbound_links': inbound,
                'outbound_links': outbound,
                'children_count': children
            })

        # sort pages by importance
        importance_scores.sort(key=lambda x: x['importance_score'], reverse=True)

        return {
            'top_important_pages': importance_scores[:30]
        }


def execute(data: List[Dict]) -> Dict:
    """
    Main execution function for pathway mapping.

    Args:
        data: List of URL dictionaries from JSONL

    Returns:
        Pathway analysis results
    """
    mapper = PathwayMapper()
    return mapper.analyze(data)


def print_summary(results: Dict):
    """Print human-readable summary of pathway analysis."""

    print("Pathway mapping summary")

    # report architecture metrics
    arch = results['architecture']
    print("Site architecture:")
    print(f"Total pages: {arch['total_pages']:,}")
    print(f"Architecture type: {arch['architecture_type'].upper()}")
    print(f"Max depth: {arch['max_depth']}")
    print(f"Average children per parent: {arch['avg_children_per_parent']:.2f}")
    print(f"Orphan pages: {arch['orphan_pages']}")

    # report entry point highlights
    entry = results['entry_points']
    print(f"Entry points: {entry['count']}")
    if entry['top_entry_points']:
        print(f"Top entry point: {entry['top_entry_points'][0]['url']}")

    # report hub statistics
    hubs = results['navigation_hubs']
    print(f"Navigation hubs: {hubs['count']}")
    if hubs['top_hubs']:
        top_hub = hubs['top_hubs'][0]
        print(f"Top hub: {top_hub['url']} ({top_hub['total_connectivity']} connections)")

    # report dead-end metrics
    dead = results['dead_ends']
    print(f"Dead ends: {dead['count']} ({dead['percentage']:.1f}%)")

    # report connectivity status
    conn = results['connectivity']
    print("Connectivity:")
    print(f"Components: {conn['total_components']}")
    print(f"Largest component: {conn['largest_component_percentage']:.1f}%")
    print(f"Isolated pages: {conn['isolated_pages']}")
