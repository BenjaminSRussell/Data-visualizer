"""Process a single URL and persist derived artifacts to storage."""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from analysis.classifiers import classify_content
from analysis.extractors import extract_features, extract_metadata, extract_text
from analysis.fetch_content import execute as fetch_url_content
from server.storage import save_classification, save_metadata, save_url

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Raised when a step in the URL processor cannot complete."""


async def execute(
    url: str,
    session_id: str,
    db: Session,
    categories: Optional[Dict[str, List[str]]] = None,
    classification_threshold: float = 0.3,
) -> Dict[str, Any]:
    """
    Process a single URL through the collection pipeline.

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
    result: Dict[str, Any] = {
        'url': url,
        'url_id': None,
        'status': 'failed',
        'error': None,
        'features': {},
        'metadata': {},
        'classifications': {}
    }

    try:
        fetch_result = await fetch_url_content(url)
        if fetch_result['error']:
            result['error'] = fetch_result['error']
            return result

        content = fetch_result['content']
        status_code = fetch_result['status_code']
        content_type = fetch_result['content_type'] or ""

        features = _extract_features(url)
        result['features'] = features

        url_id = _persist_url_record(
            db=db,
            url=url,
            session_id=session_id,
            features=features,
            status_code=status_code,
            content_type=content_type,
        )
        result['url_id'] = url_id

        if content and 'html' in content_type.lower():
            metadata = _extract_metadata(content, url)
            result['metadata'] = metadata

            if metadata:
                _persist_metadata(db, url_id, metadata)

            text_content = _extract_text(content)

            if categories and text_content:
                classifications = _classify_content(
                    url=url,
                    text=text_content,
                    categories=categories,
                    threshold=classification_threshold,
                )
                result['classifications'] = classifications

                if classifications:
                    _persist_classification(db, url_id, classifications)

        result['status'] = 'success'
        logger.info("Successfully processed %s", url)

    except ProcessingError as exc:
        logger.error("Processing error for %s: %s", url, exc)
        result['error'] = str(exc)

    return result


def execute_sync(
    url: str,
    session_id: str,
    db: Session,
    categories: Optional[Dict[str, List[str]]] = None,
    classification_threshold: float = 0.3,
) -> Dict[str, Any]:
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


def _extract_features(url: str) -> Dict[str, Any]:
    try:
        return extract_features.execute(url)
    except Exception as exc:  # noqa: BLE001 - upstream may raise domain-specific errors
        raise ProcessingError(f"Feature extraction failed for {url}: {exc}") from exc


def _persist_url_record(
    *,
    db: Session,
    url: str,
    session_id: str,
    features: Dict[str, Any],
    status_code: Optional[int],
    content_type: Optional[str],
) -> int:
    try:
        return save_url.execute(
            db=db,
            url=url,
            session_id=session_id,
            features=features,
            status_code=status_code,
            content_type=content_type,
        )
    except SQLAlchemyError as exc:
        raise ProcessingError(f"Failed to persist URL {url}: {exc}") from exc


def _extract_metadata(content: str, url: str) -> Dict[str, Any]:
    try:
        return extract_metadata.execute(content, url)
    except Exception as exc:  # noqa: BLE001 - parsers may raise external errors
        raise ProcessingError(f"Metadata extraction failed for {url}: {exc}") from exc


def _persist_metadata(db: Session, url_id: int, metadata: Dict[str, Any]) -> None:
    try:
        save_metadata.execute(db, url_id, metadata)
    except SQLAlchemyError as exc:
        raise ProcessingError(f"Failed to persist metadata for url_id={url_id}: {exc}") from exc


def _extract_text(content: str) -> str:
    try:
        return extract_text.execute(content, max_length=1000)
    except Exception as exc:  # noqa: BLE001 - text extraction may surface parser errors
        raise ProcessingError(f"Text extraction failed: {exc}") from exc


def _classify_content(
    *,
    url: str,
    text: str,
    categories: Dict[str, List[str]],
    threshold: float,
) -> Dict[str, Any]:
    try:
        combined_text = f"{url} {text[:500]}"
        return classify_content.execute(combined_text, categories, threshold=threshold)
    except Exception as exc:  # noqa: BLE001 - classification backends may vary
        raise ProcessingError(f"Classification failed for {url}: {exc}") from exc


def _persist_classification(db: Session, url_id: int, classifications: Dict[str, Any]) -> None:
    try:
        save_classification.execute(db, url_id, classifications)
    except SQLAlchemyError as exc:
        raise ProcessingError(f"Failed to persist classification for url_id={url_id}: {exc}") from exc
