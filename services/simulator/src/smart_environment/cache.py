"""Bounded in-memory result cache keyed by request hashes (B-110).

The quick estimator is deterministic: the same project hash and parameters always give the
same numbers, so a finished result can be reused instead of recomputed. The cache lives in
the local API process only, is bounded by entry count and is emptied on restart. Engine
version is part of every key, so a code change never serves a stale result.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Generic, TypeVar

T = TypeVar("T")


class ResultCache(Generic[T]):
    def __init__(self, max_entries: int) -> None:
        if max_entries < 1:
            raise ValueError("A cache needs room for at least one entry")
        self._entries: OrderedDict[str, T] = OrderedDict()
        self._lock = threading.Lock()
        self._max = max_entries
        self.hits = self.misses = 0

    def get(self, key: str) -> T | None:
        with self._lock:
            if key in self._entries:
                self._entries.move_to_end(key)
                self.hits += 1
                return self._entries[key]
            self.misses += 1
            return None

    def put(self, key: str, value: T) -> None:
        with self._lock:
            self._entries[key] = value
            self._entries.move_to_end(key)
            while len(self._entries) > self._max:
                self._entries.popitem(last=False)

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
