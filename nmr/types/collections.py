"""Typed ordered lists, independent of vocabulary and name spelling."""

import json

from pydantic import BaseModel, ConfigDict

from ..category import route
from ..pack_numbers import pair, unpair
from ..type_namer import TypeNamer


class Item(BaseModel, frozen=True):
    type: str
    value: object

    model_config = ConfigDict(extra="forbid", strict=True)


class List(TypeNamer):
    label = "list"
    description = 'Ordered typed values: [{"type":"int","value":"42"}, ...]'

    @staticmethod
    def str_to_index(value: str) -> int:
        return encode_collection(parse_collection(value), 0)

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return json.dumps(
            decode_collection(index, browse, 0),
            ensure_ascii=False,
            separators=(",", ":"),
        )


def encode_collection(value: object, depth: int) -> int:
    if depth >= MAX_DEPTH:
        raise ValueError("Collections allow at most eight nesting levels")
    if not isinstance(value, list):
        raise ValueError("A list must be a JSON array")
    if len(value) > MAX_ITEMS:
        raise ValueError("Collections allow at most 256 items")
    values = [encode_item(i, depth + 1) for i in value]
    return ((2 * pack_balanced(values) + 1) << len(values)) - 1


def parse_collection(value: str) -> object:
    try:
        return json.loads(value, object_pairs_hook=unique_fields)
    except RecursionError as error:
        raise ValueError("Collection JSON nesting exceeds the parser limit") from error


def decode_collection(index: int, browse: bool, depth: int) -> list[dict[str, object]]:
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
    return [decode_item(i, browse, depth + 1) for i in values]


def encode_item(item: object, depth: int) -> int:
    from ..registry import ROOT

    data = Item.model_validate(item)
    matches = [(p, s, c) for p, s, c in ROOT.leaves() if data.type in (p, c.label)]
    if len(matches) != 1:
        raise ValueError(f"Unknown or ambiguous item type: {data.type}")
    _, slots, codec = matches[0]
    if codec is List:
        index = encode_collection(data.value, depth)
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
        decode_collection(payload, browse, depth)
        if codec is List
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


def unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise ValueError("Duplicate JSON fields would lose information")
    return fields


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
