from pathlib import Path
import sys


def run():
    ROOT = Path(__file__).parent
    HOMOPHONES = ROOT / 'homophones.txt'
    sys.path.append(str(ROOT.parent))

    from nmbr import nmbr
    WORDS = nmbr.Nmbr.WORDS

    inverted = {word: i for i, word in enumerate(WORDS)}
    removals = set()

    with HOMOPHONES.open() as fp:
        for line in fp:
            parts = [i.lower() for i in line.strip().split(', ')]
            dupes = [i for i in parts if i in inverted]
            if len(dupes) > 1:
                _, m = min((inverted[d], d) for d in dupes)
                dupes.remove(m)
                removals.update(dupes)
                for d in dupes:
                    print('*', d, file=sys.stderr)

    words = [w for w in WORDS if w not in removals]
    print(*words, sep='\n')
    print(len(WORDS), '->', len(words), file=sys.stderr)


run()
