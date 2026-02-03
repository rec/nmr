import dataclasses as dc
import math
from collections.abc import Sequence

"""
A module for packing n numbers into a single number

TODO: see at bottom
"""


@dc.dataclass(frozen=True)
class Packer:
    count: int
    forward: bool = True

    def __post_init__(self) -> None:
        assert self.count >= 1

    def pack(self, *numbers: int) -> int:
        if len(numbers) != self.count:
            raise ValueError(f"{len(numbers)=} != {self.count=}")

        return self._pack(numbers)

    def unpack(self, n: int) -> list[int]:
        return self._unpack(n, self.count)

    def _pack(self, a: Sequence[int]) -> int:
        if len(a) == 1:
            return a[0]

        if self.forward:
            x, *rest = a
            y = self._pack(rest)
        else:
            *rest, y = a
            x = self._pack(rest)

        return _cantor(x, y)

    def _unpack(self, n: int, count: int) -> list[int]:
        if count == 1:
            return [n]

        x, y = _inverse_cantor(n)
        if self.forward:
            return [x] + self._unpack(y, count - 1)
        else:
            return self._unpack(x, count - 1) + [y]


# https://en.wikipedia.org/wiki/Pairing_function#Cantor_pairing_function


def _cantor(x: int, y: int) -> int:
    return (x + y) * (x + y + 1) // 2 + y


def _inverse_cantor(z: int) -> tuple[int, int]:
    w = int((math.sqrt(8 * z + 1) - 1) / 2)
    t = (w * w + w) // 2
    y = z - t
    x = w - y
    return x, y


if __name__ == "__main__":
    packers = (
        Packer(3, False),
        Packer(3, True),
    )

    for i in range(64):
        print(i, *(p.unpack(i) for p in packers))


"""
The results aren't very aesthetic, because the recursive definition above means some
digits increase much faster than others.

WANT something like:
[0, 0, 0]

[0, 0, 1]
[0, 1, 0]
[1, 0, 0]

[0, 0, 2]
[0, 1, 1]
[0, 2, 0]
[1, 0, 1]
[1, 1, 0]
[2, 0, 0]

[0, 0, 3]
[0, 1, 2]
[0, 2, 1]
[0, 3, 0]
[1, 0, 2]
[1, 1, 1]
[1, 2, 0]
[2, 0, 1]
[2, 1, 0]
[3, 0, 0]

[0, 0, 4]
[0, 1, 3]
[0, 2, 2]
[0, 3, 1]
[0, 4, 0]
[1, 0, 3]
[1, 1, 2]
[1, 2, 1]
[1, 3, 0]
[2, 0, 2]
[2, 1  1]
[2, 2, 0]
[3, 0, 1]
[3, 1, 0]
[4, 0, 0]

[0, 0, 0]


C(i, n)
C(0, 0) = 1

C(i, n) = sum(C(j, n-1) for j in [1, i - 1]?

[5] + i for i in

...

ACTUAL:

forward: False  True
 0 [0, 0, 0] [0, 0, 0]
 1 [1, 0, 0] [1, 0, 0]
 2 [0, 0, 1] [0, 1, 0]
 3 [0, 1, 0] [2, 0, 0]
 4 [1, 0, 1] [1, 1, 0]
 5 [0, 0, 2] [0, 0, 1]
 6 [2, 0, 0] [3, 0, 0]
 7 [0, 1, 1] [2, 1, 0]
 8 [1, 0, 2] [1, 0, 1]
 9 [0, 0, 3] [0, 2, 0]
10 [1, 1, 0] [4, 0, 0]
11 [2, 0, 1] [3, 1, 0]
12 [0, 1, 2] [2, 0, 1]
13 [1, 0, 3] [1, 2, 0]
14 [0, 0, 4] [0, 1, 1]
15 [0, 2, 0] [5, 0, 0]
16 [1, 1, 1] [4, 1, 0]
17 [2, 0, 2] [3, 0, 1]
18 [0, 1, 3] [2, 2, 0]
19 [1, 0, 4] [1, 1, 1]
20 [0, 0, 5] [0, 0, 2]
21 [3, 0, 0] [6, 0, 0]
22 [0, 2, 1] [5, 1, 0]
23 [1, 1, 2] [4, 0, 1]
24 [2, 0, 3] [3, 2, 0]
25 [0, 1, 4] [2, 1, 1]
26 [1, 0, 5] [1, 0, 2]
27 [0, 0, 6] [0, 3, 0]
28 [2, 1, 0] [7, 0, 0]
29 [3, 0, 1] [6, 1, 0]
30 [0, 2, 2] [5, 0, 1]
31 [1, 1, 3] [4, 2, 0]
32 [2, 0, 4] [3, 1, 1]
33 [0, 1, 5] [2, 0, 2]
34 [1, 0, 6] [1, 3, 0]
35 [0, 0, 7] [0, 2, 1]
36 [1, 2, 0] [8, 0, 0]
37 [2, 1, 1] [7, 1, 0]
38 [3, 0, 2] [6, 0, 1]
39 [0, 2, 3] [5, 2, 0]
40 [1, 1, 4] [4, 1, 1]
41 [2, 0, 5] [3, 0, 2]
42 [0, 1, 6] [2, 3, 0]
43 [1, 0, 7] [1, 2, 1]
44 [0, 0, 8] [0, 1, 2]
45 [0, 3, 0] [9, 0, 0]
46 [1, 2, 1] [8, 1, 0]
47 [2, 1, 2] [7, 0, 1]
48 [3, 0, 3] [6, 2, 0]
49 [0, 2, 4] [5, 1, 1]
50 [1, 1, 5] [4, 0, 2]
51 [2, 0, 6] [3, 3, 0]
52 [0, 1, 7] [2, 2, 1]
53 [1, 0, 8] [1, 1, 2]
54 [0, 0, 9] [0, 0, 3]
55 [4, 0, 0] [10, 0, 0]  # Shouldn't get to 10 for a long time...
56 [0, 3, 1] [9, 1, 0]
57 [1, 2, 2] [8, 0, 1]
58 [2, 1, 3] [7, 2, 0]
59 [3, 0, 4] [6, 1, 1]
60 [0, 2, 5] [5, 0, 2]
61 [1, 1, 6] [4, 3, 0]
62 [2, 0, 7] [3, 2, 1]
63 [0, 1, 8] [2, 1, 2]




"""
