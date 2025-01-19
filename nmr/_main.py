from __future__ import annotations

import itertools
import random
import shlex
import sys
from functools import cached_property
from pathlib import Path
from typing import Any, Iterable, NoReturn, Sequence

import dtyper

from .__main__ import nmr_main
from .nameable_type import NameableType, get_class
from .nmr import Nmr

"""See __main__.HELP"""


@dtyper.dataclass(nmr_main)
class Main:
    returncode = 0

    # Copied from nmr_main
    arguments: list[str]
    label: bool
    output_type: str | None
    raise_exceptions: bool
    random_count: int
    word_count: int | None
    word_file: Path | None

    def __call__(self) -> None:
        if self.is_pipe and self.arguments:
            raise ValueError("nmr takes no arguments when used as a pipe")
        if self.random_count and (self.arguments or self.is_pipe):
            raise ValueError("nmr takes no arguments when --random-count is set")

        lines: Iterable[str]
        if self.arguments:
            lines = [shlex.join(self.arguments)]
        elif self.is_pipe:
            lines = sys.stdin
        else:

            def _lines() -> Iterable[str]:
                while True:
                    try:
                        yield input("In:  ")
                    except EOFError:
                        return

            lines = _lines()

        for line in lines:
            if words := line.partition("#")[0].strip():
                try:
                    result = self.nmr.convert(words)
                except Exception as e:
                    if self.raise_exceptions:
                        raise
                    self.returncode = 1
                    print("ERROR:", e, file=sys.stderr)
                else:
                    if not (self.is_pipe or self.arguments):
                        print("Out: ", end="")
                    print(result)

    @cached_property
    def nmr(self) -> Nmr:
        from nmr import Nmr

        return Nmr(self.word_count, self.word_file)

    @cached_property
    def is_pipe(self) -> bool:
        return not sys.stdin.isatty()

    @cached_property
    def _type_class(self) -> type[NameableType[Any]] | None:
        if self.output_type:
            return get_class(self.output_type)
        return None

    def rnd(self) -> None:  # TODO re-enable
        for i in range(self.random_count):
            r = int(10 ** random.uniform(0, 50))
            print(f"{r}:", *self.nmr._encode_to_name(r))


def exit(*error: Any) -> NoReturn:
    if error:
        print(*error, file=sys.stderr)
    sys.exit(bool(error))
