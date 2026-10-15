"""Print a candidate vocabulary without homophones; never modify the shipped list."""

from pathlib import Path

import tyro
from pydantic import BaseModel

from nmr.words import FILE, Words


class Main(BaseModel, frozen=True):
    word_file: Path = FILE
    homophones: Path = Path(__file__).with_name("homophones.txt")

    def run(self) -> None:
        words = list(Words(self.word_file).words)
        groups = [
            i.strip().split(", ") for i in self.homophones.read_text().splitlines()
        ]
        print("\n".join(without_homophones(words, groups)))


def without_homophones(words: list[str], groups: list[list[str]]) -> list[str]:
    positions = {w: i for i, w in enumerate(words)}
    removals = set()
    for group in groups:
        matches = sorted((positions[i], i) for i in group if i in positions)
        removals.update(w for _, w in matches[1:])
    return [i for i in words if i not in removals]


if __name__ == "__main__":
    tyro.cli(Main).run()
