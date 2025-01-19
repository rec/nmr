from semver import Version

from ..categories import Computer
from ..nameable_type import NameableType
from ..pack_numbers import Packer

packer = Packer(3)


class Semver(NameableType[Version]):
    category = Computer.SEMVER

    @classmethod
    def index_to_type(cls, i: int) -> Version:
        return Version(*packer.unpack(i))

    @classmethod
    def str_to_type(cls, s: str) -> Version:
        if s.startswith("v"):
            return Version.parse(s[1:])
        raise ValueError("semantic versions must start with v")

    @staticmethod
    def type_to_index(v: Version) -> int:
        return packer.pack(v.major, v.minor, v.patch)

    @staticmethod
    def type_to_str(v: Version) -> str:
        return f"v{v}"
