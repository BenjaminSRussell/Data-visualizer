"""
Operation: Extract Clean Text

Purpose: Extract clean readable text from HTML content
Input: HTML content string
Output: Clean text string
Dependencies: BeautifulSoup4
"""

from bs4 import BeautifulSoup
import logging
import re

logger = logging.getLogger(__name__)


def execute(html_content: str, max_length: int = None) -> str:
    """
    Extract clean text from HTML content.

    Args:
        html_content: HTML content as string
        max_length: Optional maximum length of returned text

    Returns:
        Clean text string with whitespace normalized

    Example:
        text = execute(html_content, max_length=500)
        word_count = len(text.split())
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style', 'meta', 'noscript']):
            element.decompose()

        # Get text
        text = soup.get_text(separator=' ', strip=True)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length]

        return text

    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ""
