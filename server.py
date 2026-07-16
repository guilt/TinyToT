#!/usr/bin/env python3
"""Root entry point — delegates to tinytot.server."""

from tinytot.server import app, main  # noqa: F401

if __name__ == "__main__":
    main()
