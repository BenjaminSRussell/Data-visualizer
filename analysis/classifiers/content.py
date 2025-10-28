"""Classify content using zero-shot learning."""

from transformers import pipeline
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

_classifier = None
MODEL_NAME = "facebook/bart-large-mnli"


def _get_classifier():
    global _classifier
    if _classifier is None:
        logger.info(f"Loading classification model: {MODEL_NAME}")
        _classifier = pipeline("zero-shot-classification", model=MODEL_NAME)
    return _classifier


def execute(
    text: str,
    categories: Dict[str, List[str]],
    threshold: float = 0.3
) -> Dict[str, Dict[str, any]]:
    """Classify text using zero-shot model. Returns dict with label, score, and all_scores per category."""
    results = {}

    if not text or not categories:
        return results

    try:
        classifier = _get_classifier()

        for category_type, labels in categories.items():
            if not labels:
                continue

            try:
                output = classifier(
                    text[:512],
                    candidate_labels=labels,
                    multi_label=False
                )
                top_label = output['labels'][0]
                top_score = output['scores'][0]
                all_scores = dict(zip(output['labels'], output['scores']))
                if top_score >= threshold:
                    results[category_type] = {
                        'label': top_label,
                        'score': float(top_score),
                        'all_scores': {k: float(v) for k, v in all_scores.items()}
                    }
                else:
                    results[category_type] = {
                        'label': None,
                        'score': float(top_score),
                        'all_scores': {k: float(v) for k, v in all_scores.items()}
                    }
            except Exception as e:
                logger.error(f"Error classifying {category_type}: {e}")
                results[category_type] = {
                    'label': None,
                    'score': 0.0,
                    'all_scores': {},
                    'error': str(e)
                }
    except Exception as e:
        logger.error(f"Error in classification: {e}")

    return results


def execute_batch(
    texts: List[str],
    categories: Dict[str, List[str]],
    threshold: float = 0.3
) -> List[Dict[str, Dict[str, any]]]:
    """Classify multiple texts. Returns list of results."""
    return [execute(text, categories, threshold) for text in texts]


def cleanup():
    """Release classifier model from memory."""
    global _classifier
    _classifier = None
