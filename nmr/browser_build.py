"""Build a static browser tool containing the same Python codecs as the CLI."""

from importlib import metadata, util
from pathlib import Path
from shutil import copyfile
from zipfile import ZIP_DEFLATED, ZipFile


def build_browser(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    package = Path(__file__).parent
    for source in (package / "web").iterdir():
        if source.is_file():
            copyfile(source, destination / source.name)
    archive_path = destination / "python.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for name, distribution_name in [
            ("nmr", "nmr"),
            ("chess", "chess"),
            ("semver", "semver"),
            ("phonenumbers", "phonenumberslite"),
        ]:
            spec = util.find_spec(name)
            if spec is None or spec.origin is None:
                raise ValueError(f"Missing browser dependency: {name}")
            root = Path(spec.origin).parent
            for source in sorted(root.rglob("*")):
                if source.is_file() and (
                    source.suffix == ".py" or source == package / "words.txt"
                ):
                    archive.write(source, Path(name) / source.relative_to(root))
            distribution = metadata.distribution(distribution_name)
            for entry in distribution.files or []:
                if "license" in entry.name.lower() or "copying" in entry.name.lower():
                    archive.write(
                        str(distribution.locate_file(entry)),
                        Path("licenses") / name / entry.name,
                    )
    return destination / "index.html"
