"""Extract metadata from HTML: title, description, keywords, Open Graph tags, canonical URL."""

from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def execute(html_content: str, url: Optional[str] = None) -> Dict[str, any]:
    """Parse HTML and extract title, meta tags, Open Graph data, language, and canonical URL."""
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
        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text().strip()
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '').lower()
            property_val = meta.get('property', '').lower()
            content = meta.get('content', '').strip()

            if not content:
                continue
            if name == 'description':
                result['description'] = content
            elif name == 'keywords':
                result['keywords'] = [k.strip() for k in content.split(',')]
            elif name == 'author':
                result['author'] = content
            elif name == 'robots':
                result['robots'] = content
            elif property_val == 'og:title':
                result['og_title'] = content
            elif property_val == 'og:description':
                result['og_description'] = content
            elif property_val == 'og:image':
                result['og_image'] = content
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            result['language'] = html_tag.get('lang')
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            result['canonical_url'] = canonical.get('href')
    except Exception as e:
        logger.error(f"Error extracting metadata from {url or 'URL'}: {e}")

    return result
