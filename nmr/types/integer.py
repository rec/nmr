from typing import Any, Optional

from ..type_base import Type


class Integer(Type):
    @staticmethod
    def type_to_int(s: str) -> Optional[Any]:
        try:
            return int(s)
        except ValueError:
            return
