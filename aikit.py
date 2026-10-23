#!/usr/bin/env python3
"""AIKit entry point: `python aikit.py --help`. The commands live in scripts/aikit_cli.py."""

import sys

if __name__ == "__main__":
    # Help needs only the grammar. Parsing with scripts/aikit_parser.py alone prints it and exits
    # before scripts/aikit_cli.py, which imports every module the commands use, is loaded
    # (PRINCIPLE-010 R5, ADR-180). A command line that does not end in help or a usage error
    # falls through and is parsed again by main(), so behaviour is the same either way.
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        from scripts.aikit_parser import build_parser
        build_parser().parse_args(sys.argv[1:])
    from scripts.aikit_cli import main
    sys.exit(main())
