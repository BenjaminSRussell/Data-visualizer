"""
Background tasks for URL processing.
"""

from celery import Task
import logging
from typing import List, Dict, Any

from server.workers.celery_config import celery_app
from server.models import get_session, CrawlSession
from analysis.processors import sitemap_processor

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_session()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True)
async def process_sitemap_task(self, session_id: str, urls_data: List[Dict]) -> Dict[str, Any]:
    """
    Process a sitemap in the background using Celery.

    Args:
        session_id: Crawl session ID
        urls_data: List of URL dictionaries

    Returns:
        Processing summary
    """
    try:
        db = get_session()

        logger.info(f"Starting sitemap processing for session {session_id}")

        summary = await sitemap_processor.execute(
            sitemap_data=urls_data,
            session_id=session_id,
            db=db,
            max_concurrent=10
        )

        db.close()

        logger.info(f"Completed session {session_id}: {summary['processed']} processed")

        return summary

    except Exception as e:
        logger.error(f"Error in sitemap processing task: {e}")

        # Mark session as failed
        try:
            db = get_session()
            session = db.query(CrawlSession).filter(
                CrawlSession.session_id == session_id
            ).first()
            if session:
                session.status = "failed"
                db.commit()
            db.close()
        except:
            pass

        raise


@celery_app.task(base=DatabaseTask, bind=True)
def cleanup_old_sessions_task(self, days: int = 30) -> Dict[str, Any]:
    """
    Cleanup old completed sessions (maintenance task).

    Args:
        days: Delete sessions older than this many days

    Returns:
        Cleanup statistics
    """
    from datetime import datetime, timedelta

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Find old sessions
        old_sessions = self.db.query(CrawlSession).filter(
            CrawlSession.completed_at < cutoff_date,
            CrawlSession.status == 'completed'
        ).all()

        sessions_deleted = len(old_sessions)

        for session in old_sessions:
            self.db.delete(session)

        self.db.commit()

        logger.info(f"Cleanup: deleted {sessions_deleted} old sessions")

        return {
            "status": "success",
            "sessions_deleted": sessions_deleted
        }

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
