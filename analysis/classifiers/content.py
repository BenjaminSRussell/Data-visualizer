"""
Classify content using zero-shot learning.
Returns classification results with confidence scores.
"""

from transformers import pipeline
import logging
from typing import Dict, List, Optional

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
    """
    Classify text content using zero-shot learning.

    Args:
        text: Text content to classify
        categories: Dictionary mapping category types to label lists
                   Example: {"intent": ["informational", "transactional"],
                            "content_type": ["article", "product", "service"]}
        threshold: Minimum confidence threshold (0.0 to 1.0)

    Returns:
        Dictionary mapping category types to classification results:
        {
            "intent": {
                "label": "informational",
                "score": 0.85,
                "all_scores": {"informational": 0.85, "transactional": 0.15}
            },
            ...
        }

    Example:
        categories = {
            "intent": ["informational", "transactional"],
            "content_type": ["article", "product"]
        }
        results = execute(text, categories, threshold=0.5)
        print(f"Intent: {results['intent']['label']}")
    """
    results = {}

    if not text or not categories:
        return results

    try:
        classifier = _get_classifier()

        for category_type, labels in categories.items():
            if not labels:
                continue

            try:
                # Run classification
                output = classifier(
                    text[:512],  # Truncate to avoid token limits
                    candidate_labels=labels,
                    multi_label=False
                )

                # Get top result
                top_label = output['labels'][0]
                top_score = output['scores'][0]

                # Build all scores dict
                all_scores = dict(zip(output['labels'], output['scores']))

                # Only include if above threshold
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
    """
    Classify multiple texts in batch.

    Args:
        texts: List of text strings to classify
        categories: Category configuration
        threshold: Minimum confidence threshold

    Returns:
        List of classification results, one per input text

    Example:
        texts = ["Article about technology", "Buy our product now"]
        results = execute_batch(texts, categories)
    """
    return [execute(text, categories, threshold) for text in texts]


def cleanup():
    """Clean up classifier resources."""
    global _classifier
    _classifier = None
