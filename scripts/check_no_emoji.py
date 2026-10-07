#!/usr/bin/env python3
"""Fail if Python sources contain emoji code points (CI / pre-commit)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Rough emoji / pictograph ranges
_EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001f9ff"  # Misc Symbols and Pictographs, Emoticons, etc.
    "\U00002600-\U000027bf"  # Misc symbols + dingbats
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U0001fa00-\U0001faff"
    "]+"
)


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv[1:]] or list(Path(".").rglob("*.py"))
    bad = False
    for path in paths:
        if not path.is_file() or path.suffix != ".py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if _EMOJI_RE.search(line):
                print(f"{path}:{i}: emoji not allowed: {line.strip()[:80]}")
                bad = True
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
