from . import types
from . __main__ import nmbr_main
from functools import cached_property
import dtyper
import itertools
import random
import sys


def is_int(s):
    return isinstance(s, int)


def stdin_lines():
    if sys.stdin.isatty():
        return

    for line in (line for i in sys.stdin if (line := i.strip())):
        parts = [types.try_to_int(s) for s in line.split()]
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
    returncode = 0

    def __call__(self):
        self.run_lines() or self.rnd()

    @cached_property
    def nmbr(self):
        from nmbr import Nmbr

        return Nmbr(self.word_file, self.count, self.signed)

    @cached_property
    def converter(self):
        if self.output_type:
            return types.get_class(self.output_type)

    def run_lines(self):
        items = itertools.chain(self.group_args(), stdin_lines())
        return sum(self.run(i) or 1 for i in items)

    def run(self, i):
        is_int = isinstance(i, int)
        prefix = [i] if is_int else list(i)
        prefix.append(':')

        try:
            value = self.nmbr(i)
            if not is_int:
                if self.converter:
                    value = self.converter.from_int(value, i)
                value = [value]

        except Exception as e:
            if self.raise_exceptions:
                raise

            self.returncode = 1
            print('ERROR:', e, file=sys.stderr)

        else:
            if self.label:
                print(*prefix, ':', *value)
            else:
                print(*value)

    def rnd(self):
        for i in range(128):
            r = int(10 ** random.uniform(0, 50))
            print(f'{r}:', *self.nmbr(r))

    def group_args(self):
        iargs = (types.try_to_int(a) for a in self.arguments)
        for num, it in itertools.groupby(iargs, is_int):
            yield from it if num else [list(it)]
