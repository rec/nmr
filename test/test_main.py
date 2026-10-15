import io

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
    assert Main(value="universal:to").run(io.StringIO(), output, errors) == 1
    assert output.getvalue() == ""
