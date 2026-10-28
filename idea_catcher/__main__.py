"""`python -m idea_catcher`: the standalone entry point."""

import sys

from idea_catcher.registry import main

if __name__ == "__main__":
    sys.exit(main())
