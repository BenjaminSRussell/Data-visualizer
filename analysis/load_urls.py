"""Load URLs from JSONL files."""

import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


def execute(file_path: str) -> List[Dict[str, any]]:
    """Parse JSONL file and return list of URL dictionaries."""
    urls = []

    try:
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return urls

        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if isinstance(data, dict):
                        if 'url' in data:
                            urls.append(data)
                        else:
                            logger.warning(f"Line {line_num}: No 'url' field found")
                    elif isinstance(data, str):
                        urls.append({'url': data})
                    else:
                        logger.warning(f"Line {line_num}: Invalid format")
                except json.JSONDecodeError as e:
                    logger.warning(f"Line {line_num}: Invalid JSON - {e}")
                    continue

        logger.info(f"Loaded {len(urls)} URLs from {file_path}")
        return urls

    except Exception as e:
        logger.error(f"Error loading JSONL file {file_path}: {e}")
        return urls


def validate(file_path: str) -> Dict[str, any]:
    """Check JSONL file validity. Returns dict with valid flag, counts, and errors."""
    result = {
        'valid': False,
        'total_lines': 0,
        'valid_urls': 0,
        'errors': []
    }

    try:
        path = Path(file_path)

        if not path.exists():
            result['errors'].append(f"File not found: {file_path}")
            return result

        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                result['total_lines'] += 1
                line = line.strip()

                if not line:
                    continue

                try:
                    data = json.loads(line)

                    if isinstance(data, dict) and 'url' in data:
                        result['valid_urls'] += 1
                    elif isinstance(data, str):
                        result['valid_urls'] += 1
                except json.JSONDecodeError:
                    result['errors'].append(f"Line {line_num}: Invalid JSON")

        result['valid'] = result['valid_urls'] > 0

    except Exception as e:
        result['errors'].append(str(e))

    return result
