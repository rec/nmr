"""Typed ordered lists and records, independent of vocabulary and name spelling."""

import json
from typing import cast

from pydantic import BaseModel, ConfigDict

from ..category import route
from ..pack_numbers import pair, unpair
from ..type_namer import TypeNamer
from .text import Text


class Item(BaseModel, frozen=True):
    type: str
    value: object

    model_config = ConfigDict(extra="forbid", strict=True)


class List(TypeNamer):
    label = "list"
    description = 'Ordered typed values: [{"type":"int","value":"42"}, ...]'

    @staticmethod
    def str_to_index(value: str) -> int:
        return encode_collection(json.loads(value), False, 0)

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return json.dumps(
            decode_collection(index, False, browse, 0),
            ensure_ascii=False,
            separators=(",", ":"),
        )


class Record(TypeNamer):
    label = "record"
    description = (
        'Named typed fields: {"birthday":{"type":"date","value":"2000-01-01"}}'
    )

    @staticmethod
    def str_to_index(value: str) -> int:
        return encode_collection(json.loads(value), True, 0)

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return json.dumps(
            decode_collection(index, True, browse, 0),
            ensure_ascii=False,
            separators=(",", ":"),
        )


def encode_collection(value: object, record: bool, depth: int) -> int:
    if depth >= MAX_DEPTH:
        raise ValueError("Collections allow at most eight nesting levels")
    if record:
        if not isinstance(value, dict) or any(not isinstance(i, str) for i in value):
            raise ValueError("A record must be a JSON object with string keys")
        values = [
            pair(Text.str_to_index(k), encode_item(v, depth + 1))
            for k, v in sorted(cast(dict[str, object], value).items())
        ]
    else:
        if not isinstance(value, list):
            raise ValueError("A list must be a JSON array")
        values = [encode_item(i, depth + 1) for i in value]
    if len(values) > MAX_ITEMS:
        raise ValueError("Collections allow at most 256 items")
    return ((2 * pack_balanced(values) + 1) << len(values)) - 1


def decode_collection(index: int, record: bool, browse: bool, depth: int) -> object:
    if depth >= MAX_DEPTH:
        raise ValueError("Collections allow at most eight nesting levels")
    number = index + 1
    length = (number & -number).bit_length() - 1
    if length > MAX_ITEMS:
        raise ValueError("Collection index exceeds the 256-item work limit")
    packed = (number >> length) // 2
    if length == 0 and packed and not browse:
        raise ValueError("Noncanonical empty collection")
    values = unpack_balanced(packed, length)
    if record:
        result = {}
        previous: str | None = None
        for value in values:
            key_index, item_index = unpair(value)
            key = Text.index_to_str(key_index)
            if not browse and previous is not None and key <= previous:
                raise ValueError("Noncanonical record field ordering")
            previous = key
            result[key] = decode_item(item_index, browse, depth + 1)
        return dict(sorted(result.items()))
    return [decode_item(i, browse, depth + 1) for i in values]


def encode_item(item: object, depth: int) -> int:
    from ..registry import ROOT

    data = Item.model_validate(item)
    matches = [(p, s, c) for p, s, c in ROOT.leaves() if data.type in (p, c.label)]
    if len(matches) != 1:
        raise ValueError(f"Unknown or ambiguous item type: {data.type}")
    _, slots, codec = matches[0]
    if codec in (List, Record):
        index = encode_collection(data.value, codec is Record, depth)
    else:
        if not isinstance(data.value, str):
            raise ValueError("Scalar item values must be strings")
        index = codec.str_to_index(data.value)
    return route(slots, index)


def decode_item(index: int, browse: bool, depth: int) -> dict[str, object]:
    from ..registry import ROOT

    codec, payload = ROOT.resolve(index, browse)
    path = next(p for p, _, c in ROOT.leaves() if c is codec)
    value = (
        decode_collection(payload, codec is Record, browse, depth)
        if codec in (List, Record)
        else codec.index_to_str(payload, browse)
    )
    return {"type": path, "value": value}


def pack_balanced(values: list[int]) -> int:
    if not values:
        return 0
    if len(values) == 1:
        return values[0]
    middle = len(values) // 2
    return pair(pack_balanced(values[:middle]), pack_balanced(values[middle:]))


def unpack_balanced(index: int, length: int) -> list[int]:
    if length == 0:
        return []
    if length == 1:
        return [index]
    first, second = unpair(index)
    middle = length // 2
    return unpack_balanced(first, middle) + unpack_balanced(second, length - middle)


MAX_ITEMS = 256
MAX_DEPTH = 8
