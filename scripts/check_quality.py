#!/usr/bin/env python3
"""
Quick Data Quality Check

Quickly check the quality of your scraped data without running full analysis.

Usage:
    python scripts/check_quality.py [data_file]
"""

import sys
import json
import argparse
from pathlib import Path


def check_quality(data_file: str):
    """Run quick quality checks on scraped data."""

    # Load data
    data_path = Path(data_file)
    if not data_path.exists():
        print(f"Data file not found: {data_file}")
        return 1

    print(f"\nQuick quality check for {data_path.name}")

    # Load JSONL data
    data = []
    with open(data_path, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    total = len(data)
    print(f"\nTotal URLs: {total:,}")

    # Basic checks
    urls_with_title = sum(1 for item in data if item.get('title'))
    urls_with_links = sum(1 for item in data if item.get('links'))
    urls_with_errors = sum(1 for item in data if item.get('status_code', 200) >= 400)

    print("\nExtraction success:")
    print(f"  Titles extracted:  {urls_with_title:,} ({urls_with_title/total*100:.1f}%)")
    print(f"  Links extracted:   {urls_with_links:,} ({urls_with_links/total*100:.1f}%)")

    print("\nErrors:")
    print(f"  Error URLs:        {urls_with_errors:,} ({urls_with_errors/total*100:.1f}%)")

    # Duplication check
    unique_urls = len(set(item.get('url') for item in data if item.get('url')))
    duplicates = total - unique_urls
    print("\nDuplication:")
    print(f"  Unique URLs:       {unique_urls:,}")
    print(f"  Duplicate URLs:    {duplicates:,} ({duplicates/total*100:.1f}%)")

    # Overall grade
    title_score = (urls_with_title / total) * 40
    link_score = (urls_with_links / total) * 30
    error_penalty = (urls_with_errors / total) * 20
    dup_penalty = (duplicates / total) * 10

    overall_score = title_score + link_score - error_penalty - dup_penalty

    grade = 'A' if overall_score >= 90 else 'B' if overall_score >= 80 else 'C' if overall_score >= 70 else 'D' if overall_score >= 60 else 'F'

    print(f"\nOverall quality: {overall_score:.1f}/100 (Grade: {grade})")
    print()

    return 0


def main():
    parser = argparse.ArgumentParser(description='Quick data quality check')
    parser.add_argument('data_file', nargs='?', default='crawl_results.jsonl',
                       help='Path to JSONL data file')

    args = parser.parse_args()

    return check_quality(args.data_file)


if __name__ == '__main__':
    sys.exit(main())
