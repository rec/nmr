"""Shape-based recognition for the browser's single controlled input."""

import json
import re

from pydantic import BaseModel

from .category import Category, label
from .nmr import Nmr


class Recognition(BaseModel, frozen=True):
    truename: str | None = None
    kind: str | None = None
    message: str = ""


def describe_input(value: str, engine: Nmr) -> Recognition:
    if not value:
        return Recognition()
    prefix, separator, payload = value.lstrip().partition(":")
    node = None
    if separator:
        try:
            node, _ = engine.root.lookup(prefix.strip().casefold())
        except ValueError:
            pass
    if node is not None and not isinstance(node, Category):
        kind = label(node)
        try:
            payload = payload.removeprefix(" ")
            if kind == "string":
                decoded: object = json.loads(payload)
                if not isinstance(decoded, str):
                    raise ValueError("Expected a quoted string")
                payload = decoded
            result = engine.encode(payload, kind)
        except ValueError:
            return Recognition(kind=kind, message=f"Not yet a valid {kind}")
        return Recognition(truename=result.truename, kind=kind)
    kind = None
    if value.startswith("+") and any(i.isdecimal() for i in value):
        kind = "phone"
    else:
        for pattern, candidate in PATTERNS:
            if re.fullmatch(pattern, value):
                kind = candidate
                break
    if kind is None:
        if any(re.fullmatch(i, value) for i in INCOMPLETE_TYPES):
            return Recognition()
        kind = "string"
    try:
        result = engine.encode(value, kind)
    except ValueError:
        return Recognition(kind=kind, message=f"Not yet a valid {kind}")
    message = (
        "Slash pairs are fractions; use YYYY-MM-DD for dates." if kind == "frac" else ""
    )
    return Recognition(truename=result.truename, kind=kind, message=message)


PATTERNS: list[tuple[str, str]] = [
    (r"-?[0-9]+", "int"),
    (r"[+-]?[0-9]+\s*/\s*[+-]?[0-9]+", "frac"),
    (r"[0-9]{4}-[0-9]{2}-[0-9]{2}", "date"),
    (r"[0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?", "clock"),
    (r"[+-]?[0-9]+(?:\.[0-9]+)?\s*,\s*[+-]?[0-9]+(?:\.[0-9]+)?", "latlong"),
    (
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        "uuid",
    ),
    (r"[0-9]{1,3}(?:\.[0-9]{1,3}){3}", "ipv4"),
    (r"[0-9a-fA-F:.]*:[0-9a-fA-F:.]*", "ipv6"),
    (r"v?[0-9]+\.[0-9]+\.[0-9]+(?:[-+].+)?", "semver"),
    (r"-?[0-9]+(?:\.[0-9]+)?s", "duration"),
    (r"-?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)", "float"),
    (r"[0-9Xx]+(?:-[0-9Xx]+)+", "isbn"),
    (r"@.+", "tune"),
    (r"(?:9x9|13x13|19x19):.*", "go"),
    (r"(?:[a-h][1-8].*|[KQRBN][a-h1-8x].*|O-O.*)", "chess"),
    (r"\[.*\]", "list"),
]

INCOMPLETE_TYPES: list[str] = [
    r"[+@-]",
    r"\[.*",
    r"-?[0-9]+(?:\.[0-9]+)?[eE][+-]?",
    r"-?[0-9]+[./,-]",
    r"v?[0-9]+(?:\.[0-9]*){1,3}",
    r"v[0-9]+",
    r"[+-]?[0-9]+\s*/\s*[+-]?",
    r"[+-]?[0-9]+(?:\.[0-9]+)?\s*,\s*[+-]?",
    r"[KQRBN]",
]
