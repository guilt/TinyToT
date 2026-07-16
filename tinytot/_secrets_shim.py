"""
tinytot._secrets_shim — Compatibility shim for the secrets module.

The secrets module was removed in Python 3.14. This shim provides the same
interface backed by os.urandom and random.choice for older Python versions,
and is injected into sys.modules before any other import so downstream
code works unchanged.

Import this module at the top of any entry point that needs secrets:

    from tinytot._secrets_shim import ensure_secrets  # noqa: F401
"""

import os
import random
import sys


class _SecretsModule:
    """Minimal secrets module compatible with Python 3.8+."""

    @staticmethod
    def token_bytes(nbytes: int = 32) -> bytes:
        return os.urandom(nbytes)

    @staticmethod
    def token_hex(nbytes: int = 32) -> str:
        return _SecretsModule.token_bytes(nbytes).hex()

    @staticmethod
    def token_urlsafe(nbytes: int = 32) -> str:
        import base64

        return base64.urlsafe_b64encode(_SecretsModule.token_bytes(nbytes)).rstrip(b"=").decode("ascii")

    @staticmethod
    def choice(sequence):  # noqa: ANN001, ANN205
        return random.choice(sequence)

    @staticmethod
    def randbelow(exclusive_upper_bound: int) -> int:
        return random.randrange(exclusive_upper_bound)


def ensure_secrets() -> None:
    """Inject the secrets shim if the module is missing (Python 3.8+)."""
    if "secrets" not in sys.modules:
        sys.modules["secrets"] = _SecretsModule()  # type: ignore[assignment]
