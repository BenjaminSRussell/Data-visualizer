"""
Batch Detector - Identify groups of URLs with similar characteristics using MLX
"""

import mlx.core as mx
import numpy as np
from typing import List, Dict, Tuple, Set
from collections import defaultdict, Counter
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from .url_embeddings import URLEmbedder


class BatchDetector:
    """
    Detect batches of URLs using multiple strategies:
    1. Embedding-based clustering
    2. Domain/subdomain grouping
    3. Path pattern matching
    4. Temporal patterns
    5. Semantic similarity
    """

    def __init__(self, embedder: URLEmbedder = None):
        """
        Initialize batch detector.

        Args:
            embedder: Pre-trained URLEmbedder instance
        """
        self.embedder = embedder
        self.batches = []

    def detect_all_batches(self, url_data: List[Dict]) -> List[Dict]:
        """
        Run all batch detection strategies.

        Args:
            url_data: List of URL dictionaries with metadata

        Returns:
            List of detected batches with their characteristics
        """
        print(f"\nDetecting URL batches from {len(url_data):,} URLs...")

        all_batches = []

        # strategy 1: domain-based batches
        domain_batches = self._detect_domain_batches(url_data)
        all_batches.extend(domain_batches)
        print(f"  ✓ Found {len(domain_batches)} domain-based batches")

        # strategy 2: subdomain-based batches
        subdomain_batches = self._detect_subdomain_batches(url_data)
        all_batches.extend(subdomain_batches)
        print(f"  ✓ Found {len(subdomain_batches)} subdomain-based batches")

        # strategy 3: path pattern batches
        path_batches = self._detect_path_pattern_batches(url_data)
        all_batches.extend(path_batches)
        print(f"  ✓ Found {len(path_batches)} path-pattern batches")

        # strategy 4: depth-based batches
        depth_batches = self._detect_depth_batches(url_data)
        all_batches.extend(depth_batches)
        print(f"  ✓ Found {len(depth_batches)} depth-based batches")

        # strategy 5: temporal batches
        temporal_batches = self._detect_temporal_batches(url_data)
        all_batches.extend(temporal_batches)
        print(f"  ✓ Found {len(temporal_batches)} temporal batches")

        # strategy 6: embedding-based clustering (if embedder available)
        if self.embedder and self.embedder.is_trained:
            embedding_batches = self._detect_embedding_batches(url_data)
            all_batches.extend(embedding_batches)
            print(f"  ✓ Found {len(embedding_batches)} embedding-based batches")

        # strategy 7: content type batches
        content_batches = self._detect_content_type_batches(url_data)
        all_batches.extend(content_batches)
        print(f"  ✓ Found {len(content_batches)} content-type batches")

        print(f"\n✓ Total batches detected: {len(all_batches)}")

        self.batches = all_batches
        return all_batches

    def _detect_domain_batches(self, url_data: List[Dict]) -> List[Dict]:
        """Group URLs by domain"""
        from urllib.parse import urlparse

        domain_groups = defaultdict(list)

        for item in url_data:
            url = item['url']
            parsed = urlparse(url)
            domain = parsed.netloc

            domain_groups[domain].append(item)

        batches = []
        for domain, urls in domain_groups.items():
            if len(urls) >= 5:  # only create batch if >= 5 urls
                batch = {
                    'batch_name': f'domain_{domain}',
                    'batch_type': 'domain',
                    'pattern': domain,
                    'urls': urls,
                    'total_urls': len(urls),
                    'avg_depth': np.mean([u.get('depth', 0) for u in urls]),
                    'context': {
                        'grouping_criterion': 'domain',
                        'domain': domain
                    }
                }
                batches.append(batch)

        return batches

    def _detect_subdomain_batches(self, url_data: List[Dict]) -> List[Dict]:
        """Group URLs by subdomain"""
        from urllib.parse import urlparse
        import tldextract

        subdomain_groups = defaultdict(list)

        for item in url_data:
            url = item['url']
            extracted = tldextract.extract(url)
            subdomain = extracted.subdomain

            if subdomain:  # only if subdomain exists
                key = f"{subdomain}.{extracted.domain}.{extracted.suffix}"
                subdomain_groups[key].append(item)

        batches = []
        for subdomain, urls in subdomain_groups.items():
            if len(urls) >= 3:
                batch = {
                    'batch_name': f'subdomain_{subdomain}',
                    'batch_type': 'subdomain',
                    'pattern': subdomain,
                    'urls': urls,
                    'total_urls': len(urls),
                    'avg_depth': np.mean([u.get('depth', 0) for u in urls]),
                    'context': {
                        'grouping_criterion': 'subdomain',
                        'subdomain': subdomain
                    }
                }
                batches.append(batch)

        return batches

    def _detect_path_pattern_batches(self, url_data: List[Dict]) -> List[Dict]:
        """Group URLs by path patterns"""
        from urllib.parse import urlparse
        import re

        # extract path prefixes (first 2 components)
        path_groups = defaultdict(list)

        for item in url_data:
            url = item['url']
            parsed = urlparse(url)
            path = parsed.path

            # get first 2 path components
            parts = [p for p in path.split('/') if p]
            if len(parts) >= 2:
                prefix = '/' + '/'.join(parts[:2])
                path_groups[prefix].append(item)

        batches = []
        for prefix, urls in path_groups.items():
            if len(urls) >= 10:  # higher threshold for path patterns
                batch = {
                    'batch_name': f'path_{prefix.replace("/", "_")}',
                    'batch_type': 'path_pattern',
                    'pattern': prefix,
                    'urls': urls,
                    'total_urls': len(urls),
                    'avg_depth': np.mean([u.get('depth', 0) for u in urls]),
                    'context': {
                        'grouping_criterion': 'path_pattern',
                        'path_prefix': prefix
                    }
                }
                batches.append(batch)

        return batches

    def _detect_depth_batches(self, url_data: List[Dict]) -> List[Dict]:
        """Group URLs by depth"""
        depth_groups = defaultdict(list)

        for item in url_data:
            depth = item.get('depth', 0)
            depth_groups[depth].append(item)

        batches = []
        for depth, urls in depth_groups.items():
            if len(urls) >= 20:  # create batch if significant number
                batch = {
                    'batch_name': f'depth_{depth}',
                    'batch_type': 'depth',
                    'pattern': f'depth={depth}',
                    'urls': urls,
                    'total_urls': len(urls),
                    'avg_depth': depth,
                    'context': {
                        'grouping_criterion': 'depth_level',
                        'depth': depth
                    }
                }
                batches.append(batch)

        return batches

    def _detect_temporal_batches(self, url_data: List[Dict]) -> List[Dict]:
        """Group URLs by discovery time"""
        from datetime import datetime

        temporal_groups = defaultdict(list)

        for item in url_data:
            discovered_at = item.get('discovered_at')
            if discovered_at:
                # group by hour
                dt = datetime.fromtimestamp(discovered_at)
                hour_key = dt.strftime('%Y-%m-%d %H:00')
                temporal_groups[hour_key].append(item)

        batches = []
        for hour, urls in temporal_groups.items():
            if len(urls) >= 50:  # significant burst
                batch = {
                    'batch_name': f'temporal_{hour.replace(" ", "_").replace(":", "")}',
                    'batch_type': 'temporal',
                    'pattern': hour,
                    'urls': urls,
                    'total_urls': len(urls),
                    'avg_depth': np.mean([u.get('depth', 0) for u in urls]),
                    'context': {
                        'grouping_criterion': 'discovery_time',
                        'time_window': hour,
                        'description': f'URLs discovered at {hour}'
                    }
                }
                batches.append(batch)

        return batches

    def _detect_embedding_batches(self, url_data: List[Dict]) -> List[Dict]:
        """Group URLs using embedding-based clustering"""
        urls = [item['url'] for item in url_data]

        # get embeddings
        embeddings = self.embedder.embed_urls(urls)
        embeddings_np = np.array(embeddings)

        # dbscan clustering
        clustering = DBSCAN(eps=0.3, min_samples=5, metric='cosine')
        labels = clustering.fit_predict(embeddings_np)

        # group by cluster
        cluster_groups = defaultdict(list)
        for idx, label in enumerate(labels):
            if label != -1:  # ignore noise
                cluster_groups[label].append(url_data[idx])

        batches = []
        for cluster_id, urls in cluster_groups.items():
            if len(urls) >= 5:
                batch = {
                    'batch_name': f'semantic_cluster_{cluster_id}',
                    'batch_type': 'semantic_embedding',
                    'pattern': f'cluster_{cluster_id}',
                    'urls': urls,
                    'total_urls': len(urls),
                    'avg_depth': np.mean([u.get('depth', 0) for u in urls]),
                    'context': {
                        'grouping_criterion': 'embedding_similarity',
                        'cluster_id': int(cluster_id),
                        'description': 'URLs clustered by semantic similarity'
                    }
                }
                batches.append(batch)

        return batches

    def _detect_content_type_batches(self, url_data: List[Dict]) -> List[Dict]:
        """Group URLs by content type"""
        content_groups = defaultdict(list)

        for item in url_data:
            content_type = item.get('content_type', 'unknown')
            # simplify content type
            if content_type:
                main_type = content_type.split(';')[0].strip()
                content_groups[main_type].append(item)

        batches = []
        for content_type, urls in content_groups.items():
            if len(urls) >= 10:
                batch = {
                    'batch_name': f'content_{content_type.replace("/", "_")}',
                    'batch_type': 'content_type',
                    'pattern': content_type,
                    'urls': urls,
                    'total_urls': len(urls),
                    'avg_depth': np.mean([u.get('depth', 0) for u in urls]),
                    'context': {
                        'grouping_criterion': 'content_type',
                        'content_type': content_type
                    }
                }
                batches.append(batch)

        return batches

    def analyze_batch_context(self, batch: Dict) -> Dict:
        """
        Analyze what led to this batch - find common parents, patterns, etc.

        Args:
            batch: Batch dictionary

        Returns:
            Enhanced context dictionary
        """
        urls = batch['urls']

        # find common parent urls
        parents = [u.get('parent_url') for u in urls if u.get('parent_url')]
        parent_counts = Counter(parents)
        most_common_parents = parent_counts.most_common(5)

        # find common path patterns
        from urllib.parse import urlparse
        paths = [urlparse(u['url']).path for u in urls]
        path_parts = [p.split('/') for p in paths]

        # common prefixes
        common_prefixes = set()
        for parts in path_parts:
            for i in range(1, len(parts)):
                prefix = '/'.join(parts[:i])
                common_prefixes.add(prefix)

        context = batch.get('context', {})
        context.update({
            'common_parents': [
                {'url': url, 'count': count}
                for url, count in most_common_parents
            ],
            'parent_diversity': len(set(parents)),
            'description': self._generate_batch_description(batch)
        })

        return context

    def _generate_batch_description(self, batch: Dict) -> str:
        """Generate human-readable description of what defines this batch"""
        batch_type = batch['batch_type']
        pattern = batch['pattern']
        total = batch['total_urls']

        descriptions = {
            'domain': f"{total} URLs from domain '{pattern}'",
            'subdomain': f"{total} URLs from subdomain '{pattern}'",
            'path_pattern': f"{total} URLs with path pattern '{pattern}'",
            'depth': f"{total} URLs at {pattern}",
            'temporal': f"{total} URLs discovered at {pattern}",
            'semantic_embedding': f"{total} URLs with similar semantic meaning ({pattern})",
            'content_type': f"{total} URLs with content type '{pattern}'"
        }

        return descriptions.get(batch_type, f"{total} URLs matching pattern '{pattern}'")

    def get_batch_summary(self) -> Dict:
        """Get summary of all detected batches"""
        if not self.batches:
            return {'total_batches': 0}

        batch_types = Counter([b['batch_type'] for b in self.batches])
        total_urls_in_batches = sum(b['total_urls'] for b in self.batches)

        # find largest batches
        largest_batches = sorted(self.batches, key=lambda x: x['total_urls'], reverse=True)[:10]

        return {
            'total_batches': len(self.batches),
            'batch_types': dict(batch_types),
            'total_urls_in_batches': total_urls_in_batches,
            'largest_batches': [
                {
                    'name': b['batch_name'],
                    'type': b['batch_type'],
                    'pattern': b['pattern'],
                    'url_count': b['total_urls']
                }
                for b in largest_batches
            ]
        }
