"""
Operation: Extract Page Metadata

Purpose: Extract structured metadata from HTML content
Input: HTML content string
Output: Dictionary of metadata (title, description, keywords, etc.)
Dependencies: BeautifulSoup4
"""

from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def execute(html_content: str, url: Optional[str] = None) -> Dict[str, any]:
    """
    Extract metadata from HTML content.

    Args:
        html_content: HTML content as string
        url: Optional URL for logging purposes

    Returns:
        Dictionary with:
            - title: Page title
            - description: Meta description
            - keywords: List of meta keywords
            - language: Page language (from lang attribute)
            - author: Meta author
            - og_title: Open Graph title
            - og_description: Open Graph description
            - og_image: Open Graph image URL
            - canonical_url: Canonical URL
            - robots: Robots meta tag value

    Example:
        metadata = execute(html_content)
        print(f"Title: {metadata['title']}")
    """
    result = {
        'title': None,
        'description': None,
        'keywords': [],
        'language': None,
        'author': None,
        'og_title': None,
        'og_description': None,
        'og_image': None,
        'canonical_url': None,
        'robots': None
    }

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Title
        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text().strip()

        # Meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '').lower()
            property_val = meta.get('property', '').lower()
            content = meta.get('content', '').strip()

            if not content:
                continue

            # Standard meta tags
            if name == 'description':
                result['description'] = content
            elif name == 'keywords':
                result['keywords'] = [k.strip() for k in content.split(',')]
            elif name == 'author':
                result['author'] = content
            elif name == 'robots':
                result['robots'] = content

            # Open Graph tags
            elif property_val == 'og:title':
                result['og_title'] = content
            elif property_val == 'og:description':
                result['og_description'] = content
            elif property_val == 'og:image':
                result['og_image'] = content

        # Language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            result['language'] = html_tag.get('lang')

        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            result['canonical_url'] = canonical.get('href')

    except Exception as e:
        logger.error(f"Error extracting metadata from {url or 'URL'}: {e}")

    return result
