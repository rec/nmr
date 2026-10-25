"""Letter-first Unicode strings ranked by length and diagonal character tuples."""

from string import ascii_lowercase, ascii_uppercase

from ..pack_numbers import Packer
from ..type_namer import TypeNamer
from .bounded import bounded


class String(TypeNamer):
    label = "string"
    description = "Unicode text excluding C0/C1 controls, DELETE, and surrogates"

    @staticmethod
    def str_to_index(value: str) -> int:
        if not value:
            return 0
        digits = [character_index(i) for i in value]
        packed = Packer(count=len(digits)).pack(*digits)
        return ((2 * packed + 1) << len(digits)) - 1

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        if index < 0:
            raise ValueError("Expected a nonnegative string index")
        number = index + 1
        length = (number & -number).bit_length() - 1
        packed = (number >> length) // 2
        if not length:
            if packed and not browse:
                raise ValueError("Noncanonical empty string")
            return ""
        digits = Packer(count=length).unpack(packed)
        return "".join(character_from_index(i, browse) for i in digits)


def character_index(character: str) -> int:
    code = ord(character)
    if code < 0x20 or 0x7F <= code < 0xA0 or 0xD800 <= code < 0xE000:
        raise ValueError("String excludes C0/C1 controls, DELETE, and surrogates")
    if code < 0x100:
        return LOW_CHARACTERS.index(character)
    return code - 0x100 + len(LOW_CHARACTERS) - (0x800 if code >= 0xE000 else 0)


def character_from_index(index: int, browse: bool = False) -> str:
    index = bounded(index, SIZE, browse)
    if index < len(LOW_CHARACTERS):
        return LOW_CHARACTERS[index]
    code = index - len(LOW_CHARACTERS) + 0x100
    return chr(code + 0x800 if code >= 0xD800 else code)


LETTERS = ascii_lowercase + ascii_uppercase
LOW_CHARACTERS = LETTERS + "".join(
    chr(i) for i in range(0x20, 0x100) if not 0x7F <= i < 0xA0 and chr(i) not in LETTERS
)
SIZE = 0x110000 - 0x800 - 0x41
