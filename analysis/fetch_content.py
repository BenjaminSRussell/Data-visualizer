"""Fetch URL content with retry and timeout controls."""

import logging
from typing import Any, Dict, Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

_SETTINGS = get_settings()
DEFAULT_TIMEOUT = _SETTINGS.performance.request_timeout_seconds
DEFAULT_MAX_RETRIES = _SETTINGS.retries.max_retries


async def execute(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Fetch content from a URL.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        headers: Optional custom headers

    Returns:
        Dictionary with:
            - content: HTML content as string
            - status_code: HTTP status code
            - content_type: Content-Type header value
            - final_url: Final URL after redirects
            - error: Error message if failed (None on success)

    Example:
        result = await execute("https://example.com")
        if result['error'] is None:
            print(f"Fetched {len(result['content'])} bytes")
    """
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; SitemapAnalyzer/1.0)'
    }

    if headers:
        default_headers.update(headers)

    result = {
        'content': None,
        'status_code': None,
        'content_type': None,
        'final_url': url,
        'error': None
    }

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                headers=default_headers
            ) as client:
                response = await client.get(url)

                result['content'] = response.text
                result['status_code'] = response.status_code
                result['content_type'] = response.headers.get('content-type', '')
                result['final_url'] = str(response.url)

                if response.status_code >= 400:
                    result['error'] = f"HTTP {response.status_code}"
                    logger.warning(f"HTTP {response.status_code} for {url}")
                else:
                    return result

        except httpx.TimeoutException:
            result['error'] = f"Timeout after {timeout}s"
            logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{max_retries})")

        except httpx.RequestError as exc:
            result['error'] = f"Request error: {exc}"
            logger.warning(f"Request error for {url}: {exc} (attempt {attempt + 1}/{max_retries})")

    return result


def execute_sync(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Synchronous version of execute().

    Use this when you cannot use async/await.
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        execute(url, timeout, max_retries, headers)
    )
