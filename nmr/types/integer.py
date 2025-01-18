from __future__ import annotations

from typing import Any

from ..categories import Math
from ..nameable_type import NameableType


class Integer(NameableType[int]):
    category = Math.INTEGER
