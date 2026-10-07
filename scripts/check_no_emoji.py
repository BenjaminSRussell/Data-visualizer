#!/usr/bin/env python3
"""Fail if committed Python sources contain emoji characters."""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Broad emoji ranges (sufficient for forbidding decorative emoji in .py)
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "]+"
)


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv[1:]] or []
    failed = False
    for path in paths:
        if not path.exists() or path.suffix != ".py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if EMOJI_RE.search(text):
            print(f"emoji found in {path}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
