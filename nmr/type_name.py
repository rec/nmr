"""Contract shared by the codecs in the truename tree."""

from abc import ABC, abstractmethod
from typing import ClassVar


class TypeNamer(ABC):
    label: ClassVar[str]
    description: ClassVar[str]

    @staticmethod
    @abstractmethod
    def str_to_index(value: str) -> int:
        """Parse an explicit value and return its canonical nonnegative index."""

    @staticmethod
    @abstractmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        """Decode an index, rejecting noncanonical indices unless browsing."""
