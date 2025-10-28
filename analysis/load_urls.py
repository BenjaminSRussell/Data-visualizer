"""Load URLs from JSONL files."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def execute(file_path: str) -> List[Dict[str, Any]]:
    """Parse JSONL file and return list of URL dictionaries."""
    urls = []

    path = Path(file_path)

    if not path.exists():
        logger.error("File not found: %s", file_path)
        return urls

    try:
        with path.open('r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line:
                    continue
                try:
                    data: Any = json.loads(line)
                except json.JSONDecodeError as exc:
                    logger.warning("Line %s: Invalid JSON - %s", line_num, exc)
                    continue

                if isinstance(data, dict):
                    if 'url' in data and data['url']:
                        urls.append(data)
                    else:
                        logger.warning("Line %s: No 'url' field found", line_num)
                elif isinstance(data, str) and data:
                    urls.append({'url': data})
                else:
                    logger.warning("Line %s: Unsupported entry type %s", line_num, type(data).__name__)

    except OSError as exc:
        logger.error("Error loading JSONL file %s: %s", file_path, exc)
        return urls

    logger.info("Loaded %s URLs from %s", len(urls), file_path)
    return urls


def validate(file_path: str) -> Dict[str, Any]:
    """Check JSONL file validity. Returns dict with valid flag, counts, and errors."""
    result = {
        'valid': False,
        'total_lines': 0,
        'valid_urls': 0,
        'errors': []
    }

    path = Path(file_path)

    if not path.exists():
        result['errors'].append(f"File not found: {file_path}")
        return result

    try:
        with path.open('r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                result['total_lines'] += 1
                line = line.strip()

                if not line:
                    continue

                try:
                    data: Any = json.loads(line)
                except json.JSONDecodeError:
                    result['errors'].append(f"Line {line_num}: Invalid JSON")
                    continue

                if isinstance(data, dict) and data.get('url'):
                    result['valid_urls'] += 1
                elif isinstance(data, str) and data:
                    result['valid_urls'] += 1

        result['valid'] = result['valid_urls'] > 0

    except OSError as exc:
        result['errors'].append(str(exc))

    return result
