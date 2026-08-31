"""Size-aware LRU. Count bytes. Evict before load."""
from __future__ import annotations
from collections import OrderedDict
from typing import Generic, Hashable, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

class ByteLRU(Generic[K, V]):
    def __init__(self, max_bytes: int) -> None:
        self.max_bytes = max_bytes
        self._data: OrderedDict[K, tuple[V, int]] = OrderedDict()
        self._nbytes = 0

    def __len__(self) -> int:
        return len(self._data)

    @property
    def nbytes(self) -> int:
        return self._nbytes

    def get(self, key: K):
        item = self._data.get(key)
        if item is None:
            return None
        self._data.move_to_end(key)
        return item[0]

    def put(self, key: K, value: V, size: int) -> None:
        if key in self._data:
            _, old = self._data.pop(key)
            self._nbytes -= old
        self._data[key] = (value, size)
        self._nbytes += size
        self._evict()

    def _evict(self) -> None:
        while self._nbytes > self.max_bytes and self._data:
            _, (_, sz) = self._data.popitem(last=False)
            self._nbytes -= sz

    def clear(self) -> None:
        self._data.clear()
        self._nbytes = 0
