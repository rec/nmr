from __future__ import annotations

from typing import Any, Generic, TypeVar, cast, get_args

from .categories import Subcategory

DataType = TypeVar("DataType")


class TypeNamer(Generic[DataType]):
    """
    A TypeNamer describes a type that can be uniquely named by `nmr`.
    Name are never instantiated: the class has static methods that convert some o
    the `DataType` to and from strings and integer indices.

    To
    """

    category: Subcategory

    @classmethod
    def index_to_type(cls, i: int) -> DataType:
        """Given an index, construct a DataType for it, or raise a RuntimeError"""
        return cls._make(i)

    @classmethod
    def str_to_type(cls, s: str) -> DataType:
        """Given a string, construct a datatype for it or raise a RuntimeError"""
        return cls._make(s)

    @staticmethod
    def type_to_index(t: DataType) -> int:
        """Given a DataType, return an index"""
        return int(t)  # type: ignore[no-any-return, call-overload]

    @staticmethod
    def type_to_str(t: DataType) -> str:
        """Given a DataType, return a string representation of it"""
        return str(t)

    SUBCLASSES: dict[str, type[TypeNamer[Any]]] = {}

    def __init_subclass__(cls) -> None:
        name = cls.category.name.lower()
        assert name not in TypeNamer.SUBCLASSES
        TypeNamer.SUBCLASSES[name] = cls

    @classmethod
    def _make(cls, s: int | str) -> DataType:
        """Call the constructor of DataType from an int or string"""
        # https://stackoverflow.com/a/50101934/43839
        data_type = get_args(cls.__orig_bases__[0])[0]  # type: ignore[attr-defined]
        return cast(DataType, data_type(s))

    def __init__(self) -> None:
        assert False, "Cannot construct an instance of TypeNamer"


def get_class(prefix: str) -> type[TypeNamer[Any]]:
    cl = [
        c
        for c in TypeNamer.SUBCLASSES.values()
        if c.__class__.__name__.lower().startswith(prefix.lower())
    ]
    if not cl:
        raise ValueError(f"Unknown {prefix=}")
    if len(cl) > 1:
        raise ValueError(f"Ambiguous {prefix=}, could be {cl}")
    return cl[0]
