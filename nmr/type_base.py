from typing import Any, Optional


class Type:
    type = staticmethod(str)

    @classmethod
    def from_int(cls, i: int, name='str') -> str:
        c = str(cls.int_to_type(i))
        if c is not None:
            return c

        raise ValueError(f'Can\'t convert "{i}" ({name}) to {cls.__name__}')

    @classmethod
    def int_to_type(cls, i: int) -> Optional[Any]:
        return cls.type(i)

    @classmethod
    def int_to_str(cls, i: int) -> Optional[Any]:
        return str(cls.int_to_type(i))

    @staticmethod
    def type_to_int(t: Any) -> int:
        return int(t)

    @classmethod
    def to_int(cls, s: str) -> int:
        return cls.type_to_int(cls.type(s))
