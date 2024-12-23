from pathlib import Path
from typing import List, Optional

import typer
from typer import Argument, Option, Typer

from . import types

HELP = """
`nmr` is a Python program which uniquely names all canonical things, including
latlongs, fractions, numbers, IP addresses and hex numbers.

You can either pass data in from the command line, like this:

    nmr "34.5N 15:24E" 1231 -1231 1/5 "Dec 1, 2001"
    nmr boy spot dog

or you can use it as a Linux-style pipe:

   cat lines.txt | nmr

where each line gets translated independently
"""

app = Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command(help=HELP)
def nmr_main(
    arguments: list[str] = Argument(
        None, help="Things to convert to names, or vice-versa"
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
        help='Try to convert inputs to one of these output formats:'
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
