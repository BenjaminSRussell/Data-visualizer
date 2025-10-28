#!/usr/bin/env python3
"""
Cleanup Cache

Clean up various caches and temporary files.

Usage:
    python scripts/cleanup_cache.py              # Dry run
    python scripts/cleanup_cache.py --execute    # Actually delete files
"""

import argparse
import sys
from pathlib import Path


def cleanup_cache(execute: bool = False, keep_days: int = 30):
    """Clean up cache files."""

    if execute:
        print("Cache cleanup (execute mode)")
    else:
        print("Cache cleanup (dry run)")

    project_root = Path(__file__).parent.parent
    total_size = 0
    total_files = 0

    # Directories to clean
    cache_dirs = [
        project_root / '__pycache__',
        project_root / 'analysis' / '__pycache__',
        project_root / 'analysis' / 'analyzers' / '__pycache__',
        project_root / 'analysis' / 'mappers' / '__pycache__',
        project_root / 'analysis' / 'shared' / '__pycache__',
        project_root / 'analysis' / 'utils' / '__pycache__',
        project_root / 'analysis' / 'tracking' / '__pycache__',
    ]

    print("Cleaning Python cache files:")
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            for file in cache_dir.rglob('*.pyc'):
                size = file.stat().st_size
                total_size += size
                total_files += 1
                action = "Delete" if execute else "Found"
                print(f"{action} {file.relative_to(project_root)} ({size:,} bytes)")
                if execute:
                    file.unlink()

            # Remove __pycache__ directories if empty
            if execute and cache_dir.exists():
                try:
                    cache_dir.rmdir()
                    print(f"Removed empty {cache_dir.relative_to(project_root)}/")
                except OSError:
                    pass  # Directory not empty

    # Clean old metrics snapshots (optional)
    metrics_dir = project_root / 'metrics_history' / 'snapshots'
    if metrics_dir.exists():
        import time
        cutoff_time = time.time() - (keep_days * 24 * 60 * 60)

        old_snapshots = []
        for snapshot_file in metrics_dir.glob('*.json'):
            if snapshot_file.stat().st_mtime < cutoff_time:
                old_snapshots.append(snapshot_file)

        if old_snapshots:
            print(f"\nOld metric snapshots (>{keep_days} days):")
            for file in old_snapshots:
                size = file.stat().st_size
                total_size += size
                total_files += 1
                action = "Delete" if execute else "Found"
                print(f"{action} {file.name} ({size:,} bytes)")
                if execute:
                    file.unlink()

    # Summary
    print(f"Total files: {total_files}")
    print(f"Total size: {total_size / 1024:.2f} KB ({total_size:,} bytes)")

    if not execute:
        print("Run with --execute to delete these files.")
    else:
        print("Cleanup complete.")

    return 0


def main():
    parser = argparse.ArgumentParser(description='Clean up cache files')
    parser.add_argument('--execute', action='store_true',
                       help='Actually delete files (default is dry run)')
    parser.add_argument('--keep-days', type=int, default=30,
                       help='Keep metrics snapshots newer than N days')

    args = parser.parse_args()

    return cleanup_cache(args.execute, args.keep_days)


if __name__ == '__main__':
    sys.exit(main())
