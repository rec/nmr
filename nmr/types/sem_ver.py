from semver import Version

from ..categories import Computer
from ..nameable_type import NameableType

# TODO: use packed_digits when finished
BASE = 1024


class Semver(NameableType[Version]):
    category = Computer.SEMVER

    @classmethod
    def index_to_type(cls, i: int) -> Version:
        d1, m1 = divmod(i, BASE)
        d2, m2 = divmod(d1, BASE)
        d3, m3 = divmod(d2, BASE)
        if d3:
            raise ValueError("Number too large for semver")

        return Version(m3, m2, m1)

    @classmethod
    def str_to_type(cls, s: str) -> Version:
        if s.startswith("v"):
            return Version.parse(s[1:])
        raise ValueError("semantic versions must start with v")

    @staticmethod
    def type_to_index(v: Version) -> int:
        return v.patch + BASE * (v.minor + BASE * v.major)

    @staticmethod
    def type_to_str(v: Version) -> str:
        return f"v{v}"
