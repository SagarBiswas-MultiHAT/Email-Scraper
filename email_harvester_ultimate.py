#!/usr/bin/env python3
"""Backward-compatible wrapper for the new package CLI entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from email_harvester.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
