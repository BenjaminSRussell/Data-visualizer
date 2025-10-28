from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {"venv", ".venv", "__pycache__", ".git"}
EMOJI_PATTERN = re.compile("[\U0001F300-\U0001FAFF]")
TRIVIAL_COMMENT_PREFIXES = (
    re.compile(r"#\s*(Get|Set|Return|Assign|Save|Call)\b"),
)


def iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        parts = set(path.relative_to(root).parts)
        if parts & SKIP_DIRS:
            continue
        yield path


def test_repository_has_no_disallowed_patterns() -> None:
    root = Path(__file__).resolve().parents[1]
    current_file = Path(__file__).resolve()

    for path in iter_python_files(root):
        if path == current_file:
            continue
        text = path.read_text(encoding="utf-8")

        if "except Exception: pass" in text:
            raise AssertionError(f"'except Exception: pass' found in {path}")

        if "tests" in path.parts:
            continue

        if EMOJI_PATTERN.search(text):
            raise AssertionError(f"Emoji detected in {path}")

        if "analysis" in path.parts and "helpers" in path.parts:
            continue

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue
            if any(pattern.match(stripped) for pattern in TRIVIAL_COMMENT_PREFIXES):
                raise AssertionError(f"Trivial comment found in {path}: {line}")
