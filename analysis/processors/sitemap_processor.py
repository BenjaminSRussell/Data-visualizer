"""
Workflow: Process Sitemap

Purpose: Complete processing pipeline for an entire sitemap
Steps:
  1. Parse sitemap data
  2. Create crawl session
  3. Process each URL (via process_single_url workflow)
  4. Detect patterns across all URLs
  5. Update session status

Dependencies: process_single_url workflow, pattern detection
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from analysis.processors import process_single_url
from analysis.classifiers import detect_patterns
from server.storage import save_url

logger = logging.getLogger(__name__)


async def execute(
    sitemap_data: List[Dict],
    session_id: str,
    db: Session,
    categories: Optional[Dict[str, list]] = None,
    max_concurrent: int = 10
) -> Dict[str, any]:
    """
    Process an entire sitemap.

    Args:
        sitemap_data: List of URL data (strings or dicts with 'url' key)
        session_id: Crawl session ID (should already exist in DB)
        db: Database session
        categories: Classification categories
        max_concurrent: Maximum concurrent URL processing

    Returns:
        Dictionary with processing summary:
        {
            "session_id": "...",
            "total_urls": 100,
            "processed": 95,
            "failed": 5,
            "patterns": {...}
        }

    Example:
        summary = await execute(
            sitemap_data=[{"url": "https://example.com"}, ...],
            session_id=session_id,
            db=db,
            categories=categories
        )
    """
    from server.models import CrawlSession
    import asyncio

    # extract urls
    urls = [
        item.get('url') if isinstance(item, dict) else item
        for item in sitemap_data
    ]

    summary = {
        'session_id': session_id,
        'total_urls': len(urls),
        'processed': 0,
        'failed': 0,
        'patterns': {}
    }

    try:
        # get session
        session = db.query(CrawlSession).filter(
            CrawlSession.session_id == session_id
        ).first()

        if not session:
            logger.error(f"Session {session_id} not found")
            return summary

        # process urls with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(url):
            async with semaphore:
                return await url_processor.execute(
                    url=url,
                    session_id=session_id,
                    db=db,
                    categories=categories
                )

        # process all urls
        logger.info(f"Processing {len(urls)} URLs with max {max_concurrent} concurrent")
        results = await asyncio.gather(
            *[process_with_semaphore(url) for url in urls],
            return_exceptions=True
        )

        # count successes and failures
        for result in results:
            if isinstance(result, Exception):
                summary['failed'] += 1
                logger.error(f"URL processing exception: {result}")
            elif result.get('status') == 'success':
                summary['processed'] += 1
            else:
                summary['failed'] += 1

        # update session counts
        session.processed_urls = summary['processed']
        session.failed_urls = summary['failed']
        db.commit()

        # detect patterns across all urls
        logger.info("Detecting patterns across all URLs")
        patterns = detect_patterns.execute(urls)
        summary['patterns'] = detect_patterns.summarize(patterns)

        # save patterns to database
        _save_patterns_to_db(db, session_id, patterns)

        # mark session as completed
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"Sitemap processing complete: "
            f"{summary['processed']} processed, {summary['failed']} failed"
        )

    except Exception as e:
        logger.error(f"Error processing sitemap: {e}")

        # mark session as failed
        try:
            session = db.query(CrawlSession).filter(
                CrawlSession.session_id == session_id
            ).first()
            if session:
                session.status = "failed"
                db.commit()
        except:
            pass

    return summary


def _save_patterns_to_db(
    db: Session,
    session_id: str,
    patterns: Dict[str, any]
) -> None:
    """Save detected patterns to database."""
    from server.models import Pattern

    try:
        # save file type patterns
        for file_type, count in patterns['file_types'].items():
            pattern = Pattern(
                pattern_type='file_type',
                pattern_value=file_type,
                frequency=count,
                confidence=1.0,
                session_id=session_id
            )
            db.add(pattern)

        # save url structure patterns
        for structure_type, urls in patterns['url_structures'].items():
            if urls:
                pattern = Pattern(
                    pattern_type='url_structure',
                    pattern_value=structure_type,
                    frequency=len(urls),
                    confidence=0.8,
                    session_id=session_id,
                    example=urls[0] if urls else None
                )
                db.add(pattern)

        # save common prefixes
        for prefix in patterns['common_prefixes'][:10]:  # top 10
            pattern = Pattern(
                pattern_type='common_prefix',
                pattern_value=prefix,
                frequency=1,
                confidence=0.9,
                session_id=session_id
            )
            db.add(pattern)

        db.commit()

    except Exception as e:
        logger.error(f"Error saving patterns: {e}")
        db.rollback()
