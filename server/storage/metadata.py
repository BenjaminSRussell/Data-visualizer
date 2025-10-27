"""
Operation: Save Metadata

Purpose: Save page metadata to database
Input: URL ID, metadata dictionary, database session
Output: Metadata record ID
Dependencies: SQLAlchemy, models
"""

from sqlalchemy.orm import Session
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def execute(
    db: Session,
    url_id: int,
    metadata: Dict[str, any]
) -> Optional[int]:
    """
    Save page metadata.

    Args:
        db: Database session
        url_id: URL record ID
        metadata: Metadata dictionary from extract_metadata

    Returns:
        PageMetadata record ID, or None if failed

    Example:
        metadata_id = execute(db, url_id, metadata)
    """
    from server.models import PageMetadata

    try:
        # Check if metadata already exists
        page_meta = db.query(PageMetadata).filter(
            PageMetadata.url_id == url_id
        ).first()

        if page_meta:
            # Update existing metadata
            page_meta.title = metadata.get('title')
            page_meta.description = metadata.get('description')
            page_meta.keywords = metadata.get('keywords', [])
            page_meta.language = metadata.get('language')
            page_meta.author = metadata.get('author')

        else:
            # Create new metadata
            page_meta = PageMetadata(
                url_id=url_id,
                title=metadata.get('title'),
                description=metadata.get('description'),
                keywords=metadata.get('keywords', []),
                language=metadata.get('language'),
                author=metadata.get('author')
            )
            db.add(page_meta)

        db.commit()
        db.refresh(page_meta)

        return page_meta.id

    except Exception as e:
        logger.error(f"Error saving metadata for URL ID {url_id}: {e}")
        db.rollback()
        return None
