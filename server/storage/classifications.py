"""
Operation: Save Classification

Purpose: Save classification results to database
Input: URL ID, classification results, database session
Output: List of classification record IDs
Dependencies: SQLAlchemy, models
"""

from sqlalchemy.orm import Session
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

MODEL_VERSION = "facebook/bart-large-mnli"


def execute(
    db: Session,
    url_id: int,
    classifications: Dict[str, Dict[str, any]],
    model_version: str = MODEL_VERSION
) -> List[int]:
    """
    Save classification results.

    Args:
        db: Database session
        url_id: URL record ID
        classifications: Classification results from classify_content
        model_version: Model version string

    Returns:
        List of created classification record IDs

    Example:
        classification_ids = execute(db, url_id, results)
    """
    from server.models import Classification

    created_ids = []

    try:
        for category_type, result in classifications.items():
            label = result.get('label')
            score = result.get('score', 0.0)

            # Only save if there's a label
            if label and score > 0:
                classification = Classification(
                    url_id=url_id,
                    category=f"{category_type}:{label}",
                    confidence=score,
                    model_version=model_version
                )
                db.add(classification)
                db.flush()
                created_ids.append(classification.id)

        db.commit()
        return created_ids

    except Exception as e:
        logger.error(f"Error saving classifications for URL ID {url_id}: {e}")
        db.rollback()
        return []
