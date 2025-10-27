"""
Workflow: Process Single URL

Purpose: Complete processing pipeline for a single URL
Steps:
  1. Fetch URL content
  2. Extract features
  3. Extract metadata
  4. Extract text
  5. Classify content
  6. Save to database

Dependencies: All operation modules
"""

import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

# import all required operations
from analysis import fetch_url
from analysis.extractors import (
    extract_features,
    extract_metadata,
    extract_text
)
from analysis.classifiers import classify_content
from server.storage import (
    save_url,
    save_metadata,
    save_classification
)

logger = logging.getLogger(__name__)


async def execute(
    url: str,
    session_id: str,
    db: Session,
    categories: Optional[Dict[str, list]] = None,
    classification_threshold: float = 0.3
) -> Dict[str, any]:
    """
    Process a single URL through the complete pipeline.

    Args:
        url: URL to process
        session_id: Crawl session ID
        db: Database session
        categories: Classification categories
        classification_threshold: Minimum confidence for classifications

    Returns:
        Dictionary with processing results:
        {
            "url": "https://example.com",
            "url_id": 123,
            "status": "success" or "failed",
            "error": None or error message,
            "features": {...},
            "metadata": {...},
            "classifications": {...}
        }

    Example:
        result = await execute(
            "https://example.com/page.html",
            session_id,
            db,
            categories={"intent": ["informational", "transactional"]}
        )
    """
    result = {
        'url': url,
        'url_id': None,
        'status': 'failed',
        'error': None,
        'features': {},
        'metadata': {},
        'classifications': {}
    }

    try:
        # step 1: fetch url content
        logger.info(f"Fetching {url}")
        fetch_result = await fetch_url.execute(url)

        if fetch_result['error']:
            result['error'] = fetch_result['error']
            result['status'] = 'failed'
            return result

        content = fetch_result['content']
        status_code = fetch_result['status_code']
        content_type = fetch_result['content_type']

        # step 2: extract url features
        logger.info(f"Extracting features from {url}")
        features = extract_features.execute(url)
        result['features'] = features

        # step 3: save url record
        logger.info(f"Saving URL record for {url}")
        url_id = save_url.execute(
            db=db,
            url=url,
            session_id=session_id,
            features=features,
            status_code=status_code,
            content_type=content_type
        )
        result['url_id'] = url_id

        # step 4: extract and save metadata (if html content)
        if content and 'html' in content_type.lower():
            logger.info(f"Extracting metadata from {url}")
            metadata = extract_metadata.execute(content, url)
            result['metadata'] = metadata

            if metadata:
                save_metadata.execute(db, url_id, metadata)

            # step 5: extract text for classification
            logger.info(f"Extracting text from {url}")
            text_content = extract_text.execute(content, max_length=1000)

            # step 6: classify content (if categories provided)
            if categories and text_content:
                logger.info(f"Classifying {url}")

                # combine url and text for better classification
                combined_text = f"{url} {text_content[:500]}"

                classifications = classify_content.execute(
                    combined_text,
                    categories,
                    threshold=classification_threshold
                )
                result['classifications'] = classifications

                # save classifications
                if classifications:
                    save_classification.execute(db, url_id, classifications)

        result['status'] = 'success'
        logger.info(f"Successfully processed {url}")

    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        result['error'] = str(e)
        result['status'] = 'failed'

    return result


def execute_sync(
    url: str,
    session_id: str,
    db: Session,
    categories: Optional[Dict[str, list]] = None,
    classification_threshold: float = 0.3
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
        execute(url, session_id, db, categories, classification_threshold)
    )
