class Radixes:
    def __init__(self, *radixes: int) -> None:
        self.radixes = radixes

    def encode(self, *digits: int) -> int:
        total, *digits = digits
        assert len(digits) == len(self.radixes)

        for d, r in zip(digits, self.radixes):
            total = r * total + d
        return total

    def decode(self, n: int) -> list[int]:
        parts = []
        for radix in reversed(self.radixes):
            n, rem = divmod(n, radix)
            parts.append(rem)
        parts.append(n)
        return parts[::-1]
