from .convert import Convert, try_to_int
from functools import cached_property
from pathlib import Path
from typer import Argument, Option, Typer
from typing import List, Optional
import dtyper
import ipaddress
import itertools
import random
import sys
import typer

__all__ = 'Main', 'main',

HELP = """
`nmbr` is a Python module which uniquely names every number, including
IP addresses and hex numbers.
"""

app = Typer(
    add_completion=False,
    context_settings={'help_option_names': ['-h', '--help']},
)


@app.command(help=HELP)
def nmbr_main(
    to_convert: List[str] = Argument(
        None,
        help='Numbers to convert to names, or vice-versa'
    ),

    count: Optional[int] = Option(
        None, '--count', '-c',
        help='How many words from the word file to use'
    ),

    hex: bool = Option(
        False, '--hex', '-x',
        help='Output numbers in hex format (like 0xffff)'
    ),

    ip_address: bool = Option(
        False, '--ip-address', '-i',
        help='Output numbers in IP4 or IP6format, if possible'
    ),

    only_output: bool = Option(
        False, '--only-output', '-o',
        help='If true, only display the output, not the input'
    ),

    semver: bool = Option(
        False, '--semver', '-s',
        help='Print as semver'
    ),

    signed: bool = Option(
        True, '--signed/--unsigned', '-i/-u',
        help='Use unsigned numbers'
    ),

    word_file: Optional[Path] = Option(
        None, '--word-file', '-w',
        help='A file containing unique words with one word per line'
    ),
):
    Main(**locals())()


def is_int(s):
    return isinstance(s, int)


def stdin_lines():
    from nmbr import try_to_int

    if sys.stdin.isatty():
        return

    for line in (line for i in sys.stdin if (line := i.strip())):
        parts = [try_to_int(s) for s in line.split()]
        nums = sum(is_int(i) for i in parts)
        if nums == 0:
            yield parts
        elif nums == len(parts):
            yield from parts
        else:
            msg = f'Line mixes numbers and words: "{line}"'
            print(msg, file=sys.stderr)


def exit(*error):
    if error:
        print(*error, file=sys.stderr)
    sys.exit(bool(error))


@dtyper.dataclass(nmbr_main)
class Main:
    @cached_property
    def nmbr(self):
        from nmbr import Nmbr

        return Nmbr(self.word_file, self.count, self.signed)

    def convert_lines(self):
        items = itertools.chain(self.group_args(), stdin_lines())
        return sum(self.convert(i) or 1 for i in items)

    def convert(self, i):
        is_int = isinstance(i, int)
        prefix = [i] if is_int else list(i)
        prefix.append(':')

        try:
            value = self.nmbr(i) if is_int else [self.to_int(i)]
        except Exception as e:
            print('ERROR:', e, file=sys.stderr)
            raise
        else:
            if self.only_output:
                print(*prefix, ':', *value)
            else:
                print(*value)

    def rnd(self):
        for i in range(128):
            r = int(10 ** random.uniform(0, 50))
            print(f'{r}:', *self.nmbr(r))

    def group_args(self):
        iargs = (try_to_int(a) for a in self.to_convert)
        for num, it in itertools.groupby(iargs, is_int):
            yield from it if num else [list(it)]

    def to_int(self, i):
        # OBSOLETE, bad name!
        n = self.nmbr(i)

        if self.hex:
            return hex(n)

        if self.ip_address:
            try:
                return str(ipaddress.ip_address(n))
            except Exception:
                pass

        if self.semver and n >= 0:
            return Convert.Semver.from_int(n)

        return str(n)

    def __call__(self):
        self.convert_lines() or self.rnd()


def main():
    typer.main.get_command(app)()


if __name__ == '__main__':
    main()
