from pathlib import Path
from zipfile import ZipFile

from nmr.browser_build import build_browser


def test_browser_bundles_the_actual_core_and_pure_python_dependencies(
    tmp_path: Path,
) -> None:
    page = build_browser(tmp_path / "web")
    assert page.is_file()
    assert page.with_name("worker.js").is_file()
    assert page.with_name("editor.mjs").is_file()
    with ZipFile(page.with_name("python.zip")) as archive:
        assert archive.read("nmr/nmr.py") == Path("nmr/nmr.py").read_bytes()
        assert archive.read("nmr/words.txt") == Path("nmr/words.txt").read_bytes()
        assert "chess/__init__.py" in archive.namelist()
        assert "semver/__init__.py" in archive.namelist()
        assert "phonenumbers/__init__.py" in archive.namelist()
        assert "phonenumbers/data/region_GB.py" in archive.namelist()
        assert not any(
            i.startswith("phonenumbers/geodata/") for i in archive.namelist()
        )
        assert "licenses/nmr/LICENSE" in archive.namelist()
