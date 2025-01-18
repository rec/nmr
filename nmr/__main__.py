from pathlib import Path
from typing import List, Optional

import typer
from typer import Argument, Option, Typer

from . import types

HELP = """
The command line utility `nmr` can be used in three ways:

1. From the command line, with arguments

    $ nmr
    frog spot on no

    $nmr frog spot on on
    12 January 2001

2. From the command line, without arguments

   $ nmr
   In:  12 January 2001
   Out: frog spot on
   In:  17 / 21
   Out: he the word
   In: will new an
   Out: 34.5N 15:24E"

3. As a unix pipe:

    cat first.txt second.txt | nmr > out.txt

Each line is determined to be either a name, or a type, and then converted.
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
        f'{" ".join(types.names())}. Abbreviations are possible',
    ),
    raise_exceptions: bool = Option(
        False,
        "--raise-exceptions",
        "-e",
        help="If True, don't catch exceptions, allow the program to terminate",
    ),
    random_count: int = Option(0, "--random-count", "-r", help="Print random names"),
    word_count: Optional[int] = Option(
        None, "--word-count", "-c", help="How many words from the word file to use"
    ),
    word_file: Optional[Path] = Option(
        None,
        "--word-file",
        "-f",
        help="A file containing unique words with one word per line",
    ),
) -> None:
    d = dict(locals())

    from ._main import Main

    Main(**d)()


def main() -> None:
    typer.main.get_command(app)()


if __name__ == "__main__":
    main()
