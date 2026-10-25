"""Shape-based recognition for the browser's single controlled input."""

import re

from pydantic import BaseModel

from .category import label
from .nmr import Nmr


class Recognition(BaseModel, frozen=True):
    name: str | None = None
    kind: str | None = None
    name_mode: bool = False
    message: str = ""


def recognize_input(value: str, engine: Nmr, name_mode: bool = False) -> Recognition:
    original = value
    value = value.strip()
    if not value:
        return Recognition()
    words = {w.casefold(): w for w in engine.words}
    prefix, separator, payload = value.rpartition(":")
    node = None
    if separator and prefix:
        try:
            node, _ = engine.root.lookup(prefix.casefold())
        except ValueError:
            pass
    tokens = (payload if node is not None else value).split()
    if name_mode or (tokens and tokens[0].casefold() in words):
        if tokens and all(i.casefold() in words for i in tokens):
            normalized = [words[i.casefold()] for i in tokens]
            try:
                engine.decode_from_name(normalized)
            except ValueError as error:
                return Recognition(name_mode=True, message=str(error))
            name = " ".join(normalized)
            if node is not None:
                name = label(node) + ":" + name
            return Recognition(name=name, kind="name", name_mode=True)
        return Recognition(name_mode=True)
    kind = None
    if value.startswith("+") and any(i.isdecimal() for i in value):
        kind = "phone"
    else:
        for pattern, candidate in PATTERNS:
            if re.fullmatch(pattern, value):
                kind = candidate
                break
    if kind is None:
        if node is not None:
            return Recognition(kind=label(node))
        if not any(i.isspace() for i in value) and (
            any(i.startswith(value.casefold()) for i in words)
            or any(
                label(n).startswith(value.casefold()) for _, _, n in engine.root.nodes()
            )
        ):
            return Recognition()
        if any(re.fullmatch(i, value) for i in INCOMPLETE_TYPES):
            return Recognition()
        kind = "string"
    try:
        result = engine.encode(original if kind == "string" else value, kind)
    except ValueError:
        return Recognition(kind=kind, message=f"Not yet a valid {kind}")
    message = (
        "Slash pairs are fractions; use YYYY-MM-DD for dates." if kind == "frac" else ""
    )
    return Recognition(name=result.name, kind=kind, message=message)


PATTERNS: list[tuple[str, str]] = [
    (r"-?[0-9]+", "int"),
    (r"[+-]?[0-9]+\s*/\s*[+-]?[0-9]+", "frac"),
    (r"[0-9]{4}-[0-9]{2}-[0-9]{2}T.+(?:Z|[+-][0-9]{2}:[0-9]{2})", "instant"),
    (r"[0-9]{4}-[0-9]{2}-[0-9]{2}T.+", "local"),
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
