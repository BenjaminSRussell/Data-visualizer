"""
Process JSONL files containing URLs.
Loads URLs, processes them, detects patterns, and saves results.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session

from analysis import load_urls
from analysis.processors import sitemap_processor

logger = logging.getLogger(__name__)


async def execute(
    jsonl_file_path: str,
    db: Session,
    categories: Optional[Dict[str, list]] = None,
    session_name: Optional[str] = None
) -> Dict[str, any]:
    """
    Process all URLs from a JSONL file.

    Args:
        jsonl_file_path: Path to JSONL file containing URLs
        db: Database session
        categories: Optional classification categories
        session_name: Optional name for this processing session

    Returns:
        Dictionary with processing results:
        {
            "session_id": "...",
            "total_urls": 100,
            "processed": 95,
            "failed": 5,
            "patterns": {...},
            "file": "urls.jsonl"
        }

    Example:
        from analysis.processors import process_jsonl_file
        from server.models import get_session

        async def main():
            db = get_session()
            result = await process_jsonl_file.execute(
                jsonl_file_path="my_urls.jsonl",
                db=db,
                categories={"intent": ["informational", "transactional"]}
            )
            print(f"Processed {result['processed']} URLs")
            print(f"Patterns found: {result['patterns']}")
    """
    from server.models import CrawlSession

    result = {
        'session_id': None,
        'total_urls': 0,
        'processed': 0,
        'failed': 0,
        'patterns': {},
        'file': jsonl_file_path,
        'error': None
    }

    try:
        logger.info(f"Loading URLs from {jsonl_file_path}")
        urls_data = load_urls.execute(jsonl_file_path)

        if not urls_data:
            result['error'] = "No valid URLs found in file"
            return result

        result['total_urls'] = len(urls_data)
        logger.info(f"Loaded {len(urls_data)} URLs")

        # Step 2: Create crawl session
        session_id = str(uuid.uuid4())
        session_name = session_name or f"JSONL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        crawl_session = CrawlSession(
            session_id=session_id,
            total_urls=len(urls_data),
            status="processing",
            session_name=session_name
        )
        db.add(crawl_session)
        db.commit()

        result['session_id'] = session_id
        logger.info(f"Created session: {session_id}")

        logger.info("Starting URL processing...")
        summary = await sitemap_processor.execute(
            sitemap_data=urls_data,
            session_id=session_id,
            db=db,
            categories=categories,
            max_concurrent=10  # Process 10 URLs at a time
        )

        # Update result with processing summary
        result['processed'] = summary['processed']
        result['failed'] = summary['failed']
        result['patterns'] = summary.get('patterns', {})

        logger.info(
            f"Completed processing {jsonl_file_path}: "
            f"{result['processed']} processed, {result['failed']} failed"
        )

    except Exception as e:
        logger.error(f"Error processing JSONL file {jsonl_file_path}: {e}")
        result['error'] = str(e)

    return result


def execute_sync(
    jsonl_file_path: str,
    db: Session,
    categories: Optional[Dict[str, list]] = None,
    session_name: Optional[str] = None
) -> Dict[str, any]:
    """
    Synchronous version of execute().

    Use this when you cannot use async/await.
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        execute(jsonl_file_path, db, categories, session_name)
    )


def validate_file(jsonl_file_path: str) -> Dict[str, any]:
    """
    Validate JSONL file before processing.

    Args:
        jsonl_file_path: Path to JSONL file

    Returns:
        Validation results

    Example:
        validation = validate_file("urls.jsonl")
        if validation['valid']:
            print(f"File has {validation['valid_urls']} valid URLs")
        else:
            print(f"Errors: {validation['errors']}")
    """
    return load_jsonl.validate(jsonl_file_path)
