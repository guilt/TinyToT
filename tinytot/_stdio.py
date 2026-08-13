"""
tinytot._stdio — Console output helpers.

Python on Windows defaults stdout/stderr to the OEM/cp1252 code page, which
cannot represent the Unicode characters used throughout TinyToT (em-dashes,
arrows, superscripts, CJK).  Help text and log output that contain these
characters then crash with UnicodeEncodeError.

Call ensureUtf8Stdio() at the top of every CLI entry point so output is always
UTF-8 regardless of the platform's default code page.
"""

import sys


def ensureUtf8Stdio() -> None:
    """Reconfigure stdout/stderr to UTF-8 so Unicode output never crashes.

    Safe to call on any Python 3.7+ (reconfigure was added in 3.7) and on any
    stream type; the call is skipped when the stream does not support it.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except Exception:  # noqa: BLE001 — best effort only
                pass
