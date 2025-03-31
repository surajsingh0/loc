#!/usr/bin/env python3

"""
Main entry point for the Lines of Code (LOC) counter application.
"""

import sys
from app import LocCounterApp

# Ensure pathspec is installed (core dependency)
try:
    import pathspec
except ImportError:
    print("Error: 'pathspec' library not found.", file=sys.stderr)
    print("Please install it using: pip install pathspec", file=sys.stderr)
    sys.exit(1)


def run_app():
    """Initializes and runs the LocCounterApp."""
    try:
        application = LocCounterApp()
        application.run()
    except Exception as e:
        # Catch unexpected errors during app execution
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_app()
