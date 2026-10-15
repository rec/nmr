from semver import Version

from ..pack_numbers import Packer, pair, unpair
from ..type_namer import TypeNamer
from .text import rank_digits, unrank_digits


class Semver(TypeNamer):
    label = "semver"
    description = "Semantic version, including prerelease and build metadata"

    @staticmethod
    def str_to_index(value: str) -> int:
        version = Version.parse(value.removeprefix("v"))
        main = MAIN.pack(version.major, version.minor, version.patch)
        pre = metadata_index(version.prerelease or "")
        build = metadata_index(version.build or "")
        return pair(main, pair(pre, build))

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        main, extra = unpair(index)
        pre, build = unpair(extra)
        prerelease, metadata = metadata_string(pre), metadata_string(build)
        if browse:
            prerelease = (
                ".".join(
                    str(int(i)) if i.isascii() and i.isdigit() else i or "0"
                    for i in prerelease.split(".")
                )
                if prerelease
                else ""
            )
            metadata = (
                ".".join(i or "0" for i in metadata.split(".")) if metadata else ""
            )
        major, minor, patch = MAIN.unpack(main)
        value = f"{major}.{minor}.{patch}"
        if prerelease:
            value += "-" + prerelease
        if metadata:
            value += "+" + metadata
        Version.parse(value)
        return value


def metadata_index(value: str) -> int:
    return rank_digits([ALPHABET.index(i) for i in value], len(ALPHABET))


def metadata_string(index: int) -> str:
    return "".join(ALPHABET[i] for i in unrank_digits(index, len(ALPHABET)))


ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-."
MAIN = Packer(count=3)
