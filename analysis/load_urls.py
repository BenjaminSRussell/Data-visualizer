"""
Operation: Load JSONL File

Purpose: Load URLs from a JSONL file
Input: File path to JSONL file
Output: List of URL dictionaries
Dependencies: json
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


def execute(file_path: str) -> List[Dict[str, any]]:
    """
    Load URLs from a JSONL file.

    JSONL format: Each line is a JSON object
    Example line: {"url": "https://example.com", "title": "Example"}

    Args:
        file_path: Path to JSONL file

    Returns:
        List of dictionaries, each containing URL data

    Example:
        urls = execute("urls.jsonl")
        for item in urls:
            print(item['url'])
    """
    urls = []

    try:
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return urls

        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line:  # Skip empty lines
                    continue

                try:
                    data = json.loads(line)

                    # Ensure we have a URL
                    if isinstance(data, dict):
                        if 'url' in data:
                            urls.append(data)
                        else:
                            logger.warning(f"Line {line_num}: No 'url' field found")
                    elif isinstance(data, str):
                        # If just a string, treat it as a URL
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
    """
    Validate a JSONL file without loading all data.

    Args:
        file_path: Path to JSONL file

    Returns:
        Dictionary with validation results:
        {
            "valid": True/False,
            "total_lines": 10,
            "valid_urls": 9,
            "errors": []
        }
    """
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
