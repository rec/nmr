"""Build and publish nmr to https://ax.to/nmr."""

from pathlib import Path
from subprocess import run

import tyro
from pydantic import BaseModel

from nmr.browser_build import build_browser


class Deploy(BaseModel, frozen=True):
    """Upload changed browser files over SSH and set their owner and group to ax."""

    def run(self) -> None:
        destination = Path(__file__).resolve().parents[1] / "dist" / "web"
        host = "root@ax.to"
        remote = "/home/ax/public_html/nmr/"
        run(["ssh", host, "id ax >/dev/null"], check=True)
        build_browser(destination, base_path="/nmr/")
        run(["ssh", host, f"install -d -m 755 -o ax -g ax {remote}"], check=True)
        run(
            ["rsync", "-az", "--checksum", f"{destination}/", f"{host}:{remote}"],
            check=True,
        )
        run(["ssh", host, f"chown -R ax:ax {remote}"], check=True)
        print("Deployed https://ax.to/nmr")


if __name__ == "__main__":
    tyro.cli(Deploy).run()
