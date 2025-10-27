"""Process JSONL files containing URLs and save results to database."""

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
    """Load JSONL, create session, process URLs. Returns dict with session_id, counts, patterns."""
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
            max_concurrent=10
        )
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
    """Sync wrapper for execute()."""
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
    """Validate JSONL file before processing."""
    return load_jsonl.validate(jsonl_file_path)
