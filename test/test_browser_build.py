import re
from pathlib import Path
from shutil import copyfile
from zipfile import ZipFile

import pytest

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


def test_browser_assets_share_one_build_revision(tmp_path: Path) -> None:
    page = build_browser(tmp_path / "web")
    match = re.search(r"app\.js\?v=([0-9a-f]{16})", page.read_text())
    assert match is not None
    revision = match.group(1)
    assert f"style.css?v={revision}" in page.read_text()
    app = page.with_name("app.js").read_text()
    assert f"./editor.mjs?v={revision}" in app
    assert f"./tune.js?v={revision}" in app
    assert f"worker.js?v={revision}" in app
    worker = page.with_name("worker.js").read_text()
    assert f"python.zip?v={revision}" in worker
    assert f"bridge.py?v={revision}" in worker


def test_changing_a_shipped_editor_changes_its_build_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    page = build_browser(tmp_path / "before")
    before = page.read_text()
    assert build_browser(tmp_path / "same").read_text() == before

    def copy_changed_editor(source: Path, destination: Path) -> None:
        copyfile(source, destination)
        if source.name == "editor.mjs":
            destination.write_text(destination.read_text() + "\n// Changed editor\n")

    monkeypatch.setattr("nmr.browser_build.copyfile", copy_changed_editor)
    after = build_browser(tmp_path / "after")
    assert before != after.read_text()
