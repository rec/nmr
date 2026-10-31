"""Browser bridge. This file is evaluated by Pyodide, never a second codec."""

import json
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from nmr import recognition
from nmr.nmr import Nmr
from nmr.types.integer import parse_integer
from nmr.types.tune import Tune
from nmr.web.music_notation import TimeSignature, score_plan
from nmr.web.value_display import ValueAction, change_value, display_value


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
    position: Literal["start", "middle", "end"] = "middle"
    time_signature: TimeSignature = TimeSignature()


class ItemPreview(Request, frozen=True):
    absolute: bool = False
    root: int = 60
    bpm: int = 120
    position: Literal["start", "middle", "end"] = "middle"


class TruenamePreview(Preview, frozen=True):
    absolute: bool = False


class RecognitionRequest(BaseModel, frozen=True):
    value: str
    mode: Literal["description", "truename"] = "description"
    type_name: str = ""


class CountRequest(BaseModel, frozen=True):
    value: str
    type_name: str = ""
    source_type: str = ""
    source_value: str = ""
    root: int = 53
    position: Literal["start", "middle", "end"] = "middle"
    time_signature: TimeSignature = TimeSignature()


class CountActionRequest(ValueAction, frozen=True):
    value: str
    type_name: str = ""


class ItemActionRequest(ValueAction, frozen=True):
    value: str
    type_name: str
    scope: str = ""


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


def count(request_json: str) -> str:
    request = CountRequest.model_validate_json(request_json)
    index = (
        _engine.truename_index(
            _engine.encode(request.source_value, request.source_type).truename, False
        )
        if request.source_type
        else parse_integer(request.value)
    )
    truename = " ".join(_engine.to_truename(index))
    if request.type_name:
        path, _, _ = _engine.find_type(request.type_name)
        truename = path + ":" + truename
    result: dict[str, object] = {
        "index": format(Decimal(index), "f"),
        "truename": truename,
        "display": None,
    }
    try:
        decoded = _engine.decode(truename, browse=True)
    except ValueError as error:
        result["browse_error"] = str(error)
    else:
        result["browsed"] = decoded.model_dump()
        result["display"] = display_value(decoded.type, decoded.value)
        if decoded.type == "tune":
            try:
                score = score_plan(
                    Tune.from_index(index),
                    request.root,
                    request.position,
                    request.time_signature,
                )
            except ValueError as error:
                result["display"] = {"kind": "tune", "error": str(error)}
            else:
                result["display"] = {"kind": "tune", "score": score}
    return json.dumps(result)


def count_action(request_json: str) -> str:
    request = CountActionRequest.model_validate_json(request_json)
    truename = " ".join(_engine.to_truename(parse_integer(request.value)))
    if request.type_name:
        path, _, _ = _engine.find_type(request.type_name)
        truename = path + ":" + truename
    source = _engine.decode(truename, browse=True)
    value = change_value(source.type, source.value, request)
    result = _engine.encode(value, source.type, scope=request.type_name or "")
    index = _engine.truename_index(result.truename, not bool(request.type_name))
    return json.dumps({"index": format(Decimal(index), "f")})


def value_action(request_json: str) -> str:
    request = ItemActionRequest.model_validate_json(request_json)
    value = change_value(request.type_name, request.value, request)
    return _engine.encode(value, request.type_name, request.scope).model_dump_json()


def preview(request_json: str) -> str:
    request = Preview.model_validate_json(request_json)
    tune = Tune.from_text(request.value)
    if request.tie is not None:
        tune = tune.tie(request.tie)
    return render_tune(tune, request.root, request.bpm, request.position)


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
    return render_tune(tune, request.root, request.bpm, request.position)


def render_tune(
    tune: Tune,
    root: int,
    bpm: int,
    position: Literal["start", "middle", "end"] = "middle",
) -> str:
    result: dict[str, object] = {
        "value": tune.text(),
        "notes": [
            {"step": str(i.step), "duration": str(i.duration), "gap": str(i.gap)}
            for i in tune.notes
        ],
        "events": [
            {k: str(v) for k, v in i.items()} for i in tune.events(root, position)
        ],
    }
    try:
        result["playback"] = tune.playback(root, bpm, position)
    except ValueError as error:
        result["playback_error"] = str(error)
    return json.dumps(result)


def recognize(request_json: str) -> str:
    request = RecognitionRequest.model_validate_json(request_json)
    if request.type_name and request.mode == "description":
        result = _engine.encode(request.value, request.type_name, request.type_name)
        return json.dumps(
            {
                "truename": result.truename,
                "full_truename": result.truename,
                "browsed": result.model_dump(),
                "display": display_value(result.type, result.value),
            }
        )
    if request.mode == "truename":
        response: dict[str, object] = {"kind": "truename", "truename": None}
        if request.value.strip():
            try:
                value = request.value
                if request.type_name:
                    path, _, _ = _engine.find_type(request.type_name)
                    value = path + ":" + value.rsplit(":", 1)[-1]
                result = _engine.decode(value, browse=True)
                response["browsed"] = result.model_dump()
                response["display"] = display_value(result.type, result.value)
                response["truename"] = value
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
            result = _engine.decode(str(response["full_truename"]), browse=True)
            response["browsed"] = result.model_dump()
            response["display"] = display_value(result.type, result.value)
    return json.dumps(response)


def preview_truename(request_json: str) -> str:
    request = TruenamePreview.model_validate_json(request_json)
    tune = Tune.from_index(_engine.truename_index(request.value, request.absolute))
    result = json.loads(render_tune(tune, request.root, request.bpm, request.position))
    try:
        result["score"] = score_plan(
            tune, request.root, request.position, request.time_signature
        )
    except ValueError as error:
        result["score_error"] = str(error)
    return json.dumps(result)
