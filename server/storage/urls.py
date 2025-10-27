"""Save or update URL records in database."""

from sqlalchemy.orm import Session
from datetime import datetime
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def execute(
    db: Session,
    url: str,
    session_id: str,
    features: Optional[Dict[str, any]] = None,
    status_code: Optional[int] = None,
    content_type: Optional[str] = None
) -> int:
    """Save or update URL record. Returns record ID."""
    from server.models import URL

    try:
        # check if url already exists
        url_record = db.query(URL).filter(URL.url == url).first()

        if url_record:
            # update existing record
            url_record.session_id = session_id
            url_record.last_crawled = datetime.utcnow()

            if status_code:
                url_record.status_code = status_code
            if content_type:
                url_record.content_type = content_type

            if features:
                url_record.domain = features.get('domain')
                url_record.path = features.get('path')
                url_record.file_extension = features.get('file_extension')

        else:
            # create new record
            url_record = URL(
                url=url,
                session_id=session_id,
                status_code=status_code,
                content_type=content_type,
                last_crawled=datetime.utcnow()
            )

            if features:
                url_record.domain = features.get('domain')
                url_record.path = features.get('path')
                url_record.file_extension = features.get('file_extension')

            db.add(url_record)

        db.commit()
        db.refresh(url_record)

        return url_record.id

    except Exception as e:
        logger.error(f"Error saving URL {url}: {e}")
        db.rollback()
        raise
