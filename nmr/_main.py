"""Command configuration and stream processing; conversion stays in the core."""

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Literal, TextIO

import tyro
from pydantic import BaseModel, Field

from .nmr import Nmr


class Main(BaseModel):
    operation: Literal["encode", "decode", "browse"] = "decode"
    """Canonical decode is the default; browsing must be explicitly selected."""
    value: str | None = None
    """One input value. Omit to read one value per line from stdin or interactively."""
    type_name: Annotated[str | None, tyro.conf.arg(name="type")] = None
    """Type path or unique leaf name, required for encoding."""
    scope: str | None = None
    """Encoding prefix scope. Default: full leaf path. Empty string: no prefix."""
    word_file: Path | None = None
    word_count: int | None = Field(default=None, ge=1)
    case_sensitive: bool = False
    expect_vocabulary: str | None = None
    json_output: bool = False
    list_types: bool = False
    vocabulary_info: bool = False
    export_words: Path | None = None

    def run(self, source: TextIO, output: TextIO, errors: TextIO) -> int:
        engine = Nmr(self.word_file, self.word_count, not self.case_sensitive)
        if self.list_types:
            for path, description in engine.types().items():
                print(f"{path}\t{description}", file=output)
            return 0
        if self.vocabulary_info:
            print(
                json.dumps(
                    {
                        "identifier": engine.identifier,
                        "words": engine.count,
                        "maximum_payload_words": engine.count,
                    }
                ),
                file=output,
            )
            return 0
        if self.export_words is not None:
            self.export_words.write_text(engine.export())
            return 0
        if self.operation == "encode" and self.type_name is None:
            raise ValueError("Encoding requires --type")
        status = 0
        interactive = self.value is None and source.isatty()
        while True:
            if self.value is not None:
                value = self.value
            else:
                if interactive:
                    print("In: ", end="", file=errors, flush=True)
                if not (line := source.readline()):
                    break
                value = line.removesuffix("\n").removesuffix("\r")
            try:
                if self.operation == "encode":
                    result = engine.encode(value, self.type_name or "", self.scope)
                else:
                    result = engine.decode(
                        value, self.operation == "browse", self.expect_vocabulary
                    )
            except ValueError as error:
                print(f"ERROR: {error}", file=errors)
                status = 1
            else:
                if self.json_output:
                    print(result.model_dump_json(), file=output)
                else:
                    print(
                        result.name if self.operation == "encode" else result.value,
                        file=output,
                    )
                    if self.operation == "browse":
                        print(f"Canonical name: {result.name}", file=errors)
            if self.value is not None:
                break
        return status


def main(args: Sequence[str] | None = None) -> int:
    options = tyro.cli(Main, args=args)
    try:
        return options.run(sys.stdin, sys.stdout, sys.stderr)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
