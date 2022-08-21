from . _type import Type
from typing import Any, Optional


class Integer(Type):
    @staticmethod
    def type_to_int(s: str) -> Optional[Any]:
        try:
            return int(s)
        except ValueError:
            return
