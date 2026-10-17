#!/usr/bin/env python3
"""AIKit entry point: `python aikit.py --help`. The commands live in scripts/aikit_cli.py."""

import sys

from scripts.aikit_cli import main

if __name__ == "__main__":
    sys.exit(main())
