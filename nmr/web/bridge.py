"""Browser bridge. This file is evaluated by Pyodide, never a second codec."""

import json
from typing import Literal

from pydantic import BaseModel

from nmr.nmr import Nmr
from nmr.types.tune import Tune


class Settings(BaseModel, frozen=True):
    words: list[str] | None = None
    count: int | None = None
    case_sensitive: bool = False


class Request(BaseModel, frozen=True):
    operation: Literal["encode", "decode", "browse"]
    value: str
    type_name: str = ""
    scope: str | None = None
    vocabulary: str | None = None


class Preview(BaseModel, frozen=True):
    value: str
    root: int = 60
    bpm: int = 120
    tie: int | None = None


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


def preview(request_json: str) -> str:
    request = Preview.model_validate_json(request_json)
    tune = Tune.from_text(request.value)
    if request.tie is not None:
        tune = tune.tie(request.tie)
    result: dict[str, object] = {
        "value": tune.text(),
        "notes": [
            {"step": str(i.step), "duration": str(i.duration), "gap": str(i.gap)}
            for i in tune.notes
        ],
        "events": [
            {k: str(v) for k, v in i.items()} for i in tune.events(request.root)
        ],
    }
    try:
        result["playback"] = tune.playback(request.root, request.bpm)
    except ValueError as error:
        result["playback_error"] = str(error)
    return json.dumps(result)
