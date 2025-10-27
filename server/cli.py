#!/usr/bin/env python3
"""
Command-line tool to process JSONL files containing URLs.

Usage: python cli.py urls.jsonl [--name "Session Name"]

Loads URLs, fetches content, extracts metadata, classifies content,
detects patterns, and saves results to database.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.processors import batch_processor
from server.models import get_session, init_db


async def main():
    if len(sys.argv) < 2:
        print("Usage: python process_urls.py <jsonl_file> [--name <session_name>]")
        print("\nExample:")
        print("  python process_urls.py my_urls.jsonl")
        print("  python process_urls.py my_urls.jsonl --name 'My Analysis'")
        sys.exit(1)

    jsonl_file = sys.argv[1]
    session_name = None

    # Parse optional --name argument
    if len(sys.argv) > 2 and sys.argv[2] == '--name' and len(sys.argv) > 3:
        session_name = sys.argv[3]

    # Check file exists
    if not Path(jsonl_file).exists():
        print(f"Error: File not found: {jsonl_file}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Processing URLs from: {jsonl_file}")
    if session_name:
        print(f"Session name: {session_name}")
    print(f"{'='*60}\n")

    # Initialize database
    print("Initializing database...")
    init_db()

    # Get database session
    db = get_session()

    # Define categories for classification
    categories = {
        "content_type": [
            "homepage",
            "product page",
            "blog post",
            "article",
            "category page",
            "about page",
            "contact page",
            "documentation"
        ],
        "intent": [
            "informational",
            "transactional",
            "navigational"
        ]
    }

    # Validate file first
    print("Validating JSONL file...")
    validation = batch_processor.validate_file(jsonl_file)

    if not validation['valid']:
        print(f"\nFile validation failed:")
        for error in validation['errors']:
            print(f"  - {error}")
        sys.exit(1)

    print(f"Found {validation['valid_urls']} valid URLs\n")

    # Process the file
    print("Starting URL processing...")
    print("(This may take a while for large files)\n")

    result = await batch_processor.execute(
        jsonl_file_path=jsonl_file,
        db=db,
        categories=categories,
        session_name=session_name
    )

    # Display results
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print(f"{'='*60}\n")

    if result.get('error'):
        print(f"Error: {result['error']}\n")
        sys.exit(1)

    print(f"Session ID: {result['session_id']}")
    print(f"Total URLs: {result['total_urls']}")
    print(f"Successfully processed: {result['processed']}")
    print(f"Failed: {result['failed']}")

    # Display patterns
    patterns = result.get('patterns', {})
    if patterns:
        print(f"\n{'='*60}")
        print("PATTERNS DETECTED")
        print(f"{'='*60}\n")

        if 'file_types_count' in patterns:
            print(f"File types found: {patterns['file_types_count']}")

        if 'most_common_file_type' in patterns and patterns['most_common_file_type']:
            ext, count = patterns['most_common_file_type']
            print(f"Most common: .{ext} ({count} files)")

        if 'urls_with_dates' in patterns:
            print(f"URLs with dates: {patterns['urls_with_dates']}")

        if 'urls_with_ids' in patterns:
            print(f"URLs with IDs: {patterns['urls_with_ids']}")

        if 'urls_with_slugs' in patterns:
            print(f"URLs with slugs: {patterns['urls_with_slugs']}")

        if 'unique_domains' in patterns:
            print(f"Unique domains: {patterns['unique_domains']}")

    # Dashboard instructions
    print(f"\n{'='*60}")
    print("VIEW RESULTS")
    print(f"{'='*60}\n")
    print("Start the API server:")
    print("  ./run_api.sh")
    print("\nThen visit:")
    print(f"  Dashboard: http://localhost:8000/dashboard")
    print(f"  Session Results: http://localhost:8000/api/v1/sitemap/results/{result['session_id']}")
    print(f"  API Docs: http://localhost:8000/docs")
    print()

    db.close()


if __name__ == "__main__":
    asyncio.run(main())
