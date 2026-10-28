"""Build a static browser tool containing the same Python codecs as the CLI."""

from hashlib import sha256
from html import escape
from importlib import metadata, util
from pathlib import Path
from shutil import copyfile
from zipfile import ZIP_DEFLATED, ZipFile


def build_browser(destination: Path, base_path: str = "./") -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    package = Path(__file__).parent
    sources = sorted(i for i in (package / "web").iterdir() if i.is_file())
    for source in sources:
        copyfile(source, destination / source.name)
    page = destination / "index.html"
    page.write_text(
        page.read_text().replace('<base href="./"', f'<base href="{escape(base_path)}"')
    )
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
    assets = [destination / i.name for i in sources]
    digest = sha256(archive_path.read_bytes())
    for asset in assets:
        digest.update(asset.name.encode())
        digest.update(asset.read_bytes())
    revision = digest.hexdigest()[:16]
    for asset in assets:
        if asset.suffix not in {".html", ".js", ".mjs"}:
            continue
        text = asset.read_text()
        for reference in [*assets, archive_path]:
            for prefix in ["", "./"]:
                path = prefix + reference.name
                text = text.replace(f'"{path}"', f'"{path}?v={revision}"')
        asset.write_text(text)
    return destination / "index.html"
