import io
from pathlib import Path

from pytest import MonkeyPatch

from nmr._main import Main


def test_streams_preserve_hashes_and_report_each_error() -> None:
    output, errors = io.StringIO(), io.StringIO()
    status = Main(operation="encode", type_name="frac").run(
        io.StringIO("1/2\nbad#input\n0/0\n"), output, errors
    )
    assert status == 1
    assert len(output.getvalue().splitlines()) == 2
    assert "ERROR:" in errors.getvalue()


def test_canonical_decode_is_default() -> None:
    output, errors = io.StringIO(), io.StringIO()
    assert Main(value="pure:to").run(io.StringIO(), output, errors) == 1
    assert output.getvalue() == ""


def test_tune_cli_encodes_and_decodes_the_exact_phrase() -> None:
    output, errors = io.StringIO(), io.StringIO()
    assert (
        Main(operation="encode", type_name="tune", value="@1 2@1/2 r@1/3 -1@2/3").run(
            io.StringIO(), output, errors
        )
        == 0
    )
    name = output.getvalue().strip()
    decoded = io.StringIO()
    assert Main(value=name).run(io.StringIO(), decoded, errors) == 0
    assert decoded.getvalue().strip() == "@1 2@1/2 r@1/3 -1@2/3"
    assert errors.getvalue() == ""


def test_vocabulary_export_and_info(tmp_path: Path) -> None:
    import json

    from nmr.words import Words

    output, errors = io.StringIO(), io.StringIO()
    assert Main(vocabulary_info=True).run(io.StringIO(), output, errors) == 0
    info = json.loads(output.getvalue())
    assert info["words"] == 1628
    target = tmp_path / "words.txt"
    assert Main(export_words=target).run(io.StringIO(), output, errors) == 0
    assert Words(target).identifier == info["identifier"]


def test_json_pipeline_exposes_canonical_value_and_type() -> None:
    import json

    output, errors = io.StringIO(), io.StringIO()
    status = Main(
        operation="encode", type_name="date", value="2000-02-29", json_output=True
    ).run(io.StringIO(), output, errors)
    assert status == 0
    result = json.loads(output.getvalue())
    assert result["value"] == "2000-02-29"
    assert result["type"] == "real:time:date"
    assert result["canonical"] is True


def test_browsing_prints_canonical_name_to_stderr() -> None:
    output, errors = io.StringIO(), io.StringIO()
    assert (
        Main(operation="browse", value="pure:to").run(io.StringIO(), output, errors)
        == 0
    )
    assert output.getvalue().strip() == "0"
    assert "Canonical name: pure:the" in errors.getvalue()


def test_encoding_requires_an_explicit_type() -> None:
    import pytest

    with pytest.raises(ValueError, match="requires --type"):
        Main(operation="encode", value="1").run(
            io.StringIO(), io.StringIO(), io.StringIO()
        )


def test_command_entrypoint_parses_the_pydantic_model(monkeypatch: MonkeyPatch) -> None:
    import sys

    from nmr._main import main

    output, errors = io.StringIO(), io.StringIO()
    monkeypatch.setattr(sys, "stdout", output)
    monkeypatch.setattr(sys, "stderr", errors)
    assert main(["--operation", "encode", "--type", "frac", "--value", "0/0"]) == 0
    assert output.getvalue().startswith("pure:math:frac:")
    assert main(["--value", "missing:the"]) == 1
    assert "Unknown category" in errors.getvalue()
