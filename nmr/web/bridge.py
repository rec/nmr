"""Browser bridge. This file is evaluated by Pyodide, never a second codec."""

import json
from typing import Literal

from pydantic import BaseModel

from nmr.nmr import Nmr


class Settings(BaseModel):
    words: list[str] | None = None
    count: int | None = None
    case_sensitive: bool = False


class Request(BaseModel):
    operation: Literal["encode", "decode", "browse"]
    value: str
    type_name: str = ""
    scope: str | None = None
    vocabulary: str | None = None


_engine = Nmr()


def configure(settings_json: str) -> str:
    global _engine
    settings = Settings.model_validate_json(settings_json)
    engine = Nmr(settings.words, settings.count, not settings.case_sensitive)
    info = {
        "types": engine.types(),
        "identifier": engine.identifier,
        "words": engine.words,
        "count": engine.count,
    }
    _engine = engine
    return json.dumps(info, ensure_ascii=False)


def convert(request_json: str) -> str:
    request = Request.model_validate_json(request_json)
    if request.operation == "encode":
        result = _engine.encode(request.value, request.type_name, request.scope)
    else:
        result = _engine.decode(
            request.value, request.operation == "browse", request.vocabulary
        )
    return result.model_dump_json()
