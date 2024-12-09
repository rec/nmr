from __future__ import annotations

import threading


class CountWords:
    def __init__(self, n) -> None:
        self.n = n
        self._perm_count = [(1, 0)]
        self._lock = threading.Lock()

    def count(self, c: int | None = None) -> int:
        if c is None:
            c = self.n

        if len(self._perm_count) - 1 < c:
            with self._lock:
                perm, count = self._perm_count[-1]

                for i in range(len(self._perm_count) - 1, c):
                    perm *= self.n - i
                    count += perm
                    self._perm_count.append((perm, count))

        return self._perm_count[c][1]
