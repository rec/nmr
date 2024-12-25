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

"""
"""l



@dtyper.dataclass(nmr_main)
class Main:
    returncode = 0

    # Copied from nme_main
    arguments: list[str]
    raise_exceptions: bool
    count: int | None
    label: bool
    output_type: str | None
    random_count: int
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
        group_args = (i.strip() for i in " ".join(self.arguments).split(";"))
        has_items = False
        for line in itertools.chain(group_args, stdin_lines()):
            has_items = True
            try:
                if self.nmr.is_name(line):
                    result = self.nmr.name_to_type(line)
                else:
                    result = self.nmr.type_to_name(line)
            except Exception as e:
                if self.raise_exceptions:
                    raise
                self.returncode = 1
                print("ERROR:", e, file=sys.stderr)
                continue
            if self.label:
                print(f"{line}: {result}")
            else:
                print(result)

    def rnd(self) -> None:
        for i in range(self.random_count):
            r = int(10 ** random.uniform(0, 50))
            print(f"{r}:", *self.nmr._encode_to_name(r))


def stdin_lines() -> Iterator[int | str | list[int | str]]:
    if not sys.stdin.isatty():
        for line in sys.stdin:
            if (line := line.strip()) and not line.startswith("#"):
                yield line


def exit(*error: Any) -> NoReturn:
    if error:
        print(*error, file=sys.stderr)
    sys.exit(bool(error))
