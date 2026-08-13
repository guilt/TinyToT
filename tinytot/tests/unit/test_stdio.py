"""Tests for tinytot._stdio — UTF-8 console output helper."""

import io
import sys

from tinytot._stdio import ensureUtf8Stdio


class _TrackedStream(io.StringIO):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encoding = "cp1252"
        self.reconfigure_calls = []

    @property
    def encoding(self):
        return self._encoding

    def reconfigure(self, **kwargs):
        self.reconfigure_calls.append(kwargs)
        if "encoding" in kwargs:
            self._encoding = kwargs["encoding"]


class TestEnsureUtf8Stdio:
    def test_reconfigures_streams_to_utf8(self, monkeypatch):
        for name in ("stdout", "stderr"):
            original = getattr(sys, name)
            fake = _TrackedStream()
            monkeypatch.setattr(sys, name, fake)

            ensureUtf8Stdio()

            assert fake.reconfigure_calls == [{"encoding": "utf-8"}]
            monkeypatch.setattr(sys, name, original)

    def test_tolerates_stream_without_reconfigure(self, monkeypatch):
        for name in ("stdout", "stderr"):
            original = getattr(sys, name)
            fake = io.StringIO()
            monkeypatch.setattr(sys, name, fake)

            ensureUtf8Stdio()  # must not raise

            monkeypatch.setattr(sys, name, original)

    def test_tolerates_reconfigure_failure(self, monkeypatch):
        for name in ("stdout", "stderr"):
            original = getattr(sys, name)
            fake = io.StringIO()

            def boom(*_args, **_kwargs):
                raise OSError("cannot reconfigure")

            fake.reconfigure = boom
            monkeypatch.setattr(sys, name, fake)

            ensureUtf8Stdio()  # must not raise

            monkeypatch.setattr(sys, name, original)
