#!/usr/bin/env python3
"""PreToolUse hook: resale records may only be written by resale_store.py.

Records are items/<uid>-<slug>/item.yaml (for sale now), years/<yyyy>/R<n>.yaml
(closed) and years/<yyyy>/ebay_orders.json (the order ledger the 1099-K is checked
against), all under the data folder ($RESALE_BASE, default ~/resale).

The store validates the schema, holds a lock, checks a revision so two writers
can't overwrite each other, and writes atomically. A direct edit skips all of it,
so this hook blocks Write/Edit on a record and shell commands that would write one.
Reads are never blocked. Photos are plain files and are not guarded.

Bypass for a genuine rescue (a corrupt file the store itself cannot load):
RESALE_OK=1.  Exit codes: 0 allow, 2 block (stderr is shown to Claude).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

base = Path(os.environ.get("RESALE_BASE", "~/resale")).expanduser()
dir_name = re.escape(base.name)
_T = dir_name + r"/(?:items/[^/]+/item\.yaml|years/\d{4}/(?:R\d+\.yaml|ebay_orders\.json))"
RECORD = re.compile(r"(?:^|/)" + _T + r"(?:$|['\"\s])")
WRITE_SHAPES = re.compile(
    r">{1,2}\s*\S*" + _T
    + r"|\btee\b[^|;&]*" + _T
    + r"|\bsed\b[^|;&]*-i[^|;&]*" + _T
    + r"|\b(?:cp|mv|install|rsync)\b[^|;&]*" + _T
    + r"|\b(?:rm|unlink|truncate)\b[^|;&]*" + _T
)

MESSAGE = """BLOCKED: {what} writes a resale record directly.

Records have one writer, resale_store.py. Use the CLI instead, for example:
  uv run resale_store.py set R0xx price_ask=30 acquisition.price=89.99
  uv run resale_store.py sold R0xx --platform ebay --price 45 --date 2026-09-20 --order 12-34567-89012
  uv run resale_store.py kept|dispose|void R0xx --reason "..."
  uv run resale_store.py check
A non-zero exit means the write was refused: read stderr, fix the input, retry.
"""


def main() -> None:
    if os.environ.get("RESALE_OK") == "1":
        sys.exit(0)
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    tool = payload.get("tool_name", "")
    inp = payload.get("tool_input") or {}
    if tool in ("Write", "Edit", "NotebookEdit"):
        path = str(inp.get("file_path") or inp.get("notebook_path") or "")
        if RECORD.search(path + " "):
            print(MESSAGE.format(what=f"the {tool} tool"), file=sys.stderr)
            sys.exit(2)
    elif tool == "Bash" and WRITE_SHAPES.search(str(inp.get("command") or "")):
        print(MESSAGE.format(what="this shell command"), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
