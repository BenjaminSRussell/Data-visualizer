#!/usr/bin/env python3
"""
Find Duplicate URLs

Find and report duplicate URLs in your scraped data.

Usage:
    python scripts/find_duplicates.py [data_file]
    python scripts/find_duplicates.py --by-fragment
    python scripts/find_duplicates.py --by-params
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from analysis.shared.url_components import get_components, get_normalized_url


def find_duplicates(data_file: str, by_fragment: bool = False, by_params: bool = False):
    """Find duplicate URLs."""

    data_path = Path(data_file)
    if not data_path.exists():
        print(f"Data file not found: {data_file}")
        return 1

    print("Duplicate URL finder")

    # Load data
    urls = []
    with open(data_path, 'r') as f:
        for line in f:
            try:
                item = json.loads(line)
                if item.get('url'):
                    urls.append(item['url'])
            except json.JSONDecodeError:
                pass

    print(f"Total URLs: {len(urls):,}")

    # Find duplicates based on mode
    if by_fragment:
        print("Mode: fragment differences")
        groups = find_fragment_duplicates(urls)
    elif by_params:
        print("Mode: parameter differences")
        groups = find_param_duplicates(urls)
    else:
        print("Mode: exact matches")
        groups = find_exact_duplicates(urls)

    # Report results
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1}
    wasted = sum(len(v) - 1 for v in duplicate_groups.values())

    print("Results:")
    print(f"  Duplicate groups: {len(duplicate_groups):,}")
    print(f"  Wasted URLs: {wasted:,} ({wasted/len(urls)*100:.1f}%)")

    if duplicate_groups:
        print("Top duplicate clusters:")
        sorted_groups = sorted(duplicate_groups.items(), key=lambda x: len(x[1]), reverse=True)

        for i, (base, urls_list) in enumerate(sorted_groups[:10], 1):
            print(f"{i}. {len(urls_list)} duplicates")
            print(f"   Base: {base}")
            for url in urls_list[:3]:
                print(f"     {url}")
            if len(urls_list) > 3:
                remaining = len(urls_list) - 3
                print(f"     ... {remaining} more")

    return 0


def find_exact_duplicates(urls):
    """Find exact duplicate URLs."""
    groups = defaultdict(list)
    for url in urls:
        groups[url].append(url)
    return groups


def find_fragment_duplicates(urls):
    """Find URLs that differ only by fragment."""
    groups = defaultdict(list)
    for url in urls:
        normalized = get_normalized_url(url, remove_fragment=True, remove_tracking=False)
        groups[normalized].append(url)
    return groups


def find_param_duplicates(urls):
    """Find URLs that differ only by parameters."""
    groups = defaultdict(list)
    for url in urls:
        components = get_components(url)
        base = f"{components['scheme']}://{components['netloc']}{components['path']}"
        groups[base].append(url)
    return groups


def main():
    parser = argparse.ArgumentParser(description='Find duplicate URLs')
    parser.add_argument('data_file', nargs='?', default='crawl_results.jsonl',
                       help='Path to JSONL data file')
    parser.add_argument('--by-fragment', action='store_true',
                       help='Find URLs differing only by fragment')
    parser.add_argument('--by-params', action='store_true',
                       help='Find URLs differing only by parameters')

    args = parser.parse_args()

    return find_duplicates(args.data_file, args.by_fragment, args.by_params)


if __name__ == '__main__':
    sys.exit(main())
