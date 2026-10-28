"""Browser bridge. This file is evaluated by Pyodide, never a second codec."""

import json
from typing import Literal

from pydantic import BaseModel

from nmr import recognition
from nmr.nmr import Nmr
from nmr.types.tune import Tune


class Settings(BaseModel, frozen=True):
    words: list[str] | None = None
    count: int | None = None
    case_sensitive: bool = False
    center_on_zoot: bool = True


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


class ItemPreview(Request, frozen=True):
    absolute: bool = False
    root: int = 60
    bpm: int = 120


class TruenamePreview(Preview, frozen=True):
    absolute: bool = False


class RecognitionRequest(BaseModel, frozen=True):
    value: str
    mode: Literal["description", "truename"] = "description"


_engine = Nmr()


def configure(settings_json: str) -> str:
    global _engine
    settings = Settings.model_validate_json(settings_json)
    engine = Nmr(
        settings.words,
        settings.count,
        not settings.case_sensitive,
        center_on_zoot=settings.center_on_zoot,
    )
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
    return render_tune(tune, request.root, request.bpm)


def preview_item(request_json: str) -> str:
    request = ItemPreview.model_validate_json(request_json)
    if request.vocabulary is not None and request.vocabulary != _engine.identifier:
        raise ValueError("Vocabulary identifier does not match the selected list")
    truename = (
        _engine.encode(request.value, request.type_name, request.scope).truename
        if request.operation == "encode"
        else request.value
    )
    tune = _engine.to_tune(truename, request.absolute, request.operation == "browse")
    return render_tune(tune, request.root, request.bpm)


def render_tune(tune: Tune, root: int, bpm: int) -> str:
    result: dict[str, object] = {
        "value": tune.text(),
        "notes": [
            {"step": str(i.step), "duration": str(i.duration), "gap": str(i.gap)}
            for i in tune.notes
        ],
        "events": [{k: str(v) for k, v in i.items()} for i in tune.events(root)],
    }
    try:
        result["playback"] = tune.playback(root, bpm)
    except ValueError as error:
        result["playback_error"] = str(error)
    return json.dumps(result)


def recognize(request_json: str) -> str:
    request = RecognitionRequest.model_validate_json(request_json)
    if request.mode == "truename":
        response: dict[str, object] = {"kind": "truename", "truename": None}
        if request.value.strip():
            try:
                result = _engine.decode(request.value, browse=True)
                response["browsed"] = result.model_dump()
                response["truename"] = request.value
            except ValueError as error:
                response["browse_error"] = str(error)
    else:
        description = recognition.describe_input(request.value, _engine)
        response = description.model_dump()
        response["full_truename"] = None
        if description.truename:
            response["full_truename"] = " ".join(
                _engine.to_truename(_engine.truename_index(description.truename))
            )
    return json.dumps(response)


def preview_truename(request_json: str) -> str:
    request = TruenamePreview.model_validate_json(request_json)
    tune = Tune.from_index(_engine.truename_index(request.value, request.absolute))
    return render_tune(tune, request.root, request.bpm)
