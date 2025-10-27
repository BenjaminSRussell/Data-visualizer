"""
URL Normalizer - Remove fragments, deduplicate, clean URLs

Based on diagnostic evidence:
- Removes fragments (reduces dataset by 52%)
- Deduplicates base URLs
- Merges metadata from fragment variations
- Normalizes path components
"""

import hashlib
from urllib.parse import urlparse, urlunparse, parse_qs
from typing import List, Dict, Optional
from collections import defaultdict
import tldextract


class URLNormalizer:
    """Normalize and deduplicate URLs"""

    def __init__(self):
        self.normalization_stats = {
            'total_input': 0,
            'total_output': 0,
            'fragments_removed': 0,
            'duplicates_merged': 0,
            'urls_cleaned': 0
        }

    def normalize_url(self, url: str, remove_fragment=True, remove_query=False) -> str:
        """
        Normalize a single URL.

        Args:
            url: URL string
            remove_fragment: Remove fragment (#anchor)
            remove_query: Remove query parameters

        Returns:
            Normalized URL
        """
        parsed = urlparse(url)

        # build normalized url components
        scheme = parsed.scheme.lower() if parsed.scheme else 'https'
        netloc = parsed.netloc.lower()
        path = parsed.path

        # remove trailing slash except for root
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')

        # optionally remove fragment
        fragment = '' if remove_fragment else parsed.fragment

        # optionally remove query
        query = '' if remove_query else parsed.query

        normalized = urlunparse((scheme, netloc, path, '', query, fragment))

        return normalized

    def get_url_hash(self, url: str) -> str:
        """Generate SHA256 hash of normalized URL"""
        normalized = self.normalize_url(url)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def normalize_batch(self, url_data: List[Dict],
                        remove_fragments=True,
                        merge_metadata=True) -> List[Dict]:
        """
        Normalize a batch of URLs and merge duplicates.

        Args:
            url_data: List of URL dictionaries
            remove_fragments: Remove URL fragments
            merge_metadata: Merge metadata from duplicate URLs

        Returns:
            List of normalized, deduplicated URLs
        """
        self.normalization_stats['total_input'] = len(url_data)

        # group entries by normalized url
        url_groups = defaultdict(list)

        for item in url_data:
            url = item['url']
            normalized = self.normalize_url(url, remove_fragment=remove_fragments)

            url_groups[normalized].append(item)

        # merge duplicate url entries
        normalized_urls = []

        for normalized_url, items in url_groups.items():
            if len(items) == 1:
                # use entry unchanged when unique
                merged = items[0].copy()
                merged['url'] = normalized_url
                merged['url_hash'] = self.get_url_hash(normalized_url)
            else:
                # merge duplicate entries
                merged = self._merge_duplicate_urls(normalized_url, items, merge_metadata)
                self.normalization_stats['duplicates_merged'] += len(items) - 1

            if urlparse(merged['url']).fragment != urlparse(items[0]['url']).fragment:
                self.normalization_stats['fragments_removed'] += 1

            normalized_urls.append(merged)

        self.normalization_stats['total_output'] = len(normalized_urls)
        self.normalization_stats['urls_cleaned'] = len(normalized_urls)

        return normalized_urls

    def _merge_duplicate_urls(self, normalized_url: str,
                             duplicates: List[Dict],
                             merge_metadata: bool) -> Dict:
        """
        Merge multiple URL entries into one.

        Strategy:
        - Use the entry with the most complete data
        - Merge link arrays
        - Keep best quality metadata
        """
        # select the most complete entry
        best_entry = max(duplicates, key=lambda x: (
            bool(x.get('content_type')),
            bool(x.get('title')),
            len(x.get('links', [])),
            -x.get('depth', 999)  # prefer shallower depth
        ))

        merged = best_entry.copy()
        merged['url'] = normalized_url
        merged['url_hash'] = self.get_url_hash(normalized_url)

        if merge_metadata:
            # compile fragments
            all_fragments = [urlparse(d['url']).fragment for d in duplicates if urlparse(d['url']).fragment]
            if all_fragments:
                merged['fragments'] = list(set(all_fragments))

            # combine links without duplicates
            all_links = []
            for d in duplicates:
                all_links.extend(d.get('links', []))
            merged['links'] = list(set(all_links))

            # keep earliest discovery time
            discovery_times = [d.get('discovered_at') for d in duplicates if d.get('discovered_at')]
            if discovery_times:
                merged['discovered_at'] = min(discovery_times)

            # track duplicate counts
            merged['merged_count'] = len(duplicates)
            merged['source_urls'] = [d['url'] for d in duplicates]

        return merged

    def extract_components(self, url: str) -> Dict:
        """
        Extract detailed URL components using tldextract.

        Returns:
            Dictionary with URL components
        """
        parsed = urlparse(url)
        extracted = tldextract.extract(url)

        components = {
            # basic components
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'path': parsed.path,
            'query': parsed.query,
            'fragment': parsed.fragment,

            # domain components from tldextract
            'subdomain': extracted.subdomain,
            'domain': extracted.domain,
            'suffix': extracted.suffix,  # tld
            'registered_domain': extracted.registered_domain,  # domain.suffix
            'fqdn': extracted.fqdn,  # fully qualified domain name

            # path components
            'path_segments': [s for s in parsed.path.split('/') if s],
            'path_depth': len([s for s in parsed.path.split('/') if s]),

            # query components
            'query_params': dict(parse_qs(parsed.query)) if parsed.query else {},
            'query_param_count': len(parse_qs(parsed.query)) if parsed.query else 0,

            # file information
            'filename': parsed.path.split('/')[-1] if parsed.path.split('/')[-1] else None,
            'file_extension': parsed.path.split('.')[-1] if '.' in parsed.path.split('/')[-1] else None,
        }

        return components

    def get_stats(self) -> Dict:
        """Get normalization statistics"""
        return self.normalization_stats.copy()

    def print_stats(self):
        """Print normalization statistics"""
        stats = self.normalization_stats

        print("\n" + "="*80)
        print("URL NORMALIZATION STATISTICS")
        print("="*80)
        print(f"  Input URLs: {stats['total_input']:,}")
        print(f"  Output URLs: {stats['total_output']:,}")
        print(f"  Reduction: {stats['total_input'] - stats['total_output']:,} URLs ({(stats['total_input'] - stats['total_output']) / stats['total_input'] * 100:.1f}%)")
        print(f"  Fragments removed: {stats['fragments_removed']:,}")
        print(f"  Duplicates merged: {stats['duplicates_merged']:,}")
        print("="*80 + "\n")


def normalize_jsonl_file(input_file: str, output_file: str, remove_fragments=True):
    """
    Normalize URLs in a JSONL file.

    Args:
        input_file: Input JSONL file path
        output_file: Output JSONL file path
        remove_fragments: Whether to remove URL fragments
    """
    import json

    # load urls
    urls = []
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                urls.append(json.loads(line))

    print(f"Loaded {len(urls):,} URLs from {input_file}")

    # normalize urls
    normalizer = URLNormalizer()
    normalized = normalizer.normalize_batch(urls, remove_fragments=remove_fragments)

    # save normalized output
    with open(output_file, 'w') as f:
        for item in normalized:
            f.write(json.dumps(item) + '\n')

    print(f"Saved {len(normalized):,} normalized URLs to {output_file}")

    # print normalization stats
    normalizer.print_stats()

    return normalized
