class Radixes:
    def __init__(self, *radixes: int) -> None:
        self.radixes = radixes

    def encode(self, *digits: int) -> int:
        total, *digit = digits
        assert len(digit) == len(self.radixes)

        for d, r in zip(digit, self.radixes, strict=False):
            total = r * total + d
        return total

    def decode(self, n: int) -> list[int]:
        parts = []
        for radix in reversed(self.radixes):
            n, rem = divmod(n, radix)
            parts.append(rem)
        parts.append(n)
        return parts[::-1]
