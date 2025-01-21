from semver import Version

from ..categories import Computer
from ..pack_numbers import Packer
from ..type_namer import TypeNamer

packer = Packer(3)


class Semver(TypeNamer[Version]):
    category = Computer.SEMVER

    @staticmethod
    def index_to_type(i: int) -> Version:
        return Version(*packer.unpack(i))

    @staticmethod
    def str_to_type(s: str) -> Version:
        if s.startswith("v"):
            return Version.parse(s[1:])
        raise ValueError("semantic versions must start with v")

    @staticmethod
    def type_to_index(v: Version) -> int:
        return packer.pack(v.major, v.minor, v.patch)

    @staticmethod
    def type_to_str(v: Version) -> str:
        return f"v{v}"
