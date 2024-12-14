from __future__ import annotations

import itertools
import random
import sys
from functools import cached_property
from pathlib import Path
from typing import Any, Iterator, NoReturn, Sequence

import dtyper

from . import types
from .__main__ import nmr_main
from .nameable_type import NameableType
from .nmr import Nmr


def is_int(s: Any) -> bool:
    return isinstance(s, int)


def stdin_lines() -> Iterator[int | str | list[int | str]]:
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


def exit(*error: Any) -> NoReturn:
    if error:
        print(*error, file=sys.stderr)
    sys.exit(bool(error))


@dtyper.dataclass(nmr_main)
class Main:
    returncode = 0

    # Copied from nme_main
    arguments: list[str]
    raise_exceptions: bool
    count: int | None
    label: bool
    output_type: str | None
    word_file: Path | None

    def __call__(self) -> None:
        if not self.run_lines():
            self.rnd()

    @cached_property
    def nmr(self) -> Nmr:
        from nmr import Nmr

        return Nmr(self.count, self.word_file)

    @cached_property
    def _type_class(self) -> type[NameableType] | None:
        if self.output_type:
            return types.get_class(self.output_type)
        return None

    def run_lines(self) -> bool:
        items = itertools.chain(self.group_args(), stdin_lines())
        has_items = False
        for i in items:
            self.run(i)
            has_items = True
        return has_items

    def run(self, i: Any) -> None:
        value: Sequence[Any]
        try:
            if self._type_class and isinstance(i, int):
                value = [i]
            else:
                value = self.nmr.encode_to_name(i)

            if self._type_class:
                value = [self._type_class.int_to_str(v) for v in value]

        except Exception as e:
            if self.raise_exceptions:
                raise

            self.returncode = 1
            print("!!!!!", e, type(e), e.args)
            print("ERROR:", e, file=sys.stderr)
            return

        prefix = [i] if isinstance(i, int) else list(i)
        if self.label:
            print(*prefix, ":", *value)
        else:
            print(*value)

    def rnd(self) -> None:
        for i in range(128):
            r = int(10 ** random.uniform(0, 50))
            print(f"{r}:", *self.nmr.encode_to_name(r))

    def group_args(self) -> Iterator[int | str | list[int | str]]:
        iargs = (types.try_to_int(a) for a in self.arguments or ())
        for num, it in itertools.groupby(iargs, is_int):
            if num:
                yield from it
            else:
                yield from [list(it)]
