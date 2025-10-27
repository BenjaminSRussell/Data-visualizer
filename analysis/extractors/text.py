"""Extract clean text from HTML, removing scripts and styles."""

from bs4 import BeautifulSoup
import logging
import re

logger = logging.getLogger(__name__)


def execute(html_content: str, max_length: int = None) -> str:
    """Remove HTML tags and extract text with normalized whitespace."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for element in soup(['script', 'style', 'meta', 'noscript']):
            element.decompose()
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        if max_length and len(text) > max_length:
            text = text[:max_length]
        return text
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ""
