from pathlib import Path
from typing import List, Optional

import typer
from typer import Argument, Option, Typer

from . import types

HELP = """
`nmbr` is a Python module which uniquely names every number, including
IP addresses and hex numbers.
"""

app = Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command(help=HELP)
def nmr_main(
    arguments: list[str] = Argument(
        None, help="Numbers to convert to names, or vice-versa"
    ),
    raise_exceptions: bool = Option(
        False,
        "--raise-exceptions",
        "-e",
        help="If True, don't catch exceptions, allow the program to terminate",
    ),
    count: Optional[int] = Option(
        None, "--count", "-c", help="How many words from the word file to use"
    ),
    label: bool = Option(
        False,
        "--label",
        "-l",
        help="If true, display the input as a label to the output",
    ),
    output_type: Optional[str] = Option(
        None,
        "--output-type",
        "-t",
        help='Try to convert outputs to one of these formats:'
        f'{" ".join(types.NAMES)}. Abbreviations are possible',
    ),
    random_count: int = Option(
        10, "--random-count", "-r", help="How many random numbers to print"
    ),
    word_file: Optional[Path] = Option(
        None,
        "--word-file",
        "-w",
        help="A file containing unique words with one word per line",
    ),
) -> None:
    d = dict(locals())

    from ._main import Main

    Main(**d)()


def main():
    typer.main.get_command(app)()


if __name__ == "__main__":
    main()
