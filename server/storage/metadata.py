"""Save page metadata to database."""

from sqlalchemy.orm import Session
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def execute(
    db: Session,
    url_id: int,
    metadata: Dict[str, any]
) -> Optional[int]:
    """Save page metadata to database. Returns record ID or None."""
    from server.models import PageMetadata

    try:
        page_meta = db.query(PageMetadata).filter(PageMetadata.url_id == url_id).first()
        if page_meta:
            # update existing metadata
            page_meta.title = metadata.get('title')
            page_meta.description = metadata.get('description')
            page_meta.keywords = metadata.get('keywords', [])
            page_meta.language = metadata.get('language')
            page_meta.author = metadata.get('author')

        else:
            # create new metadata
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
