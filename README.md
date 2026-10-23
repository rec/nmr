# nmr

Give exact details reversible names made from ordinary words. Name a birthday,
short tune, phone number, coordinate, fraction, identifier, or legal chess game,
then let a friend recover it with the same vocabulary.

A name contains a readable type prefix and a payload without repeated words:

```text
real:time:date:nor lung
```

That name means `2000-02-29`. Canonical decoding is the default. Browsing is an
explicit operation for discovering objects from other word combinations.

## Install and try

Requires Python 3.10 or newer and [uv](https://docs.astral.sh/uv/).
This checkout contains the new 1.0 format; it has not been published to PyPI.

```sh
git clone git@github.com:rec/nmr.git
cd nmr
uv sync --frozen
uv run --frozen nmr --operation encode --type date --value 2000-02-29
uv run --frozen nmr --value 'real:time:date:nor lung'
```

To install the CLI outside the checkout, run `uv tool install .`.
Use `nmr --help` for the complete options and `nmr --list-types` for type paths.
Frozen development commands use the checked-in package versions independently of
machine-local resolution settings. Regenerate the lock deliberately when changing
dependencies.

## Encode, decode, and browse

```sh
# Preserve the actual fraction pair, including zero denominators.
nmr --operation encode --type frac --value '2/4'
# pure:math:frac:now
nmr --value 'pure:math:frac:now'
# 2/4

# The scope controls how much type information stays in the word payload.
nmr --operation encode --type chess --value 'e4 e5 Nf3'
# play:game:chess:in get
nmr --operation encode --type chess --value 'e4 e5 Nf3' --scope play
# play:both pride
nmr --operation encode --type chess --value 'e4 e5 Nf3' --scope ''
# sons paint

# Explore a noncanonical name. The stable name is printed to stderr.
nmr --operation browse --value 'pure:to'
# 0
# Canonical name: pure:the

# One value per line; errors go to stderr and produce exit status 1.
printf '2000-02-29\n2024-12-31\n' | nmr --operation encode --type date

# JSON includes type, canonical value, name, vocabulary ID, and canonical status.
nmr --operation encode --type phone --value '+442079460958' --json-output
```

Without `--value`, the CLI reads stdin, or prompts when used in a terminal.
`--value` preserves its entire argument, including whitespace, `#`, and newlines.
There is no implicit type guessing or country inference.

Canonical decoding rejects unassigned type slots, invalid values, and
noncanonical encodings. It never silently switches to browsing. Browsing may
redirect those indices, returns a real supported object, and supplies its
canonical name. Exploratory inputs can discover different objects as the tree
expands; save the canonical output instead.

## Supported details

| Type or path | Input and identity |
| --- | --- |
| `int` | Signed decimal integer, including very large integers within vocabulary capacity. |
| `frac` | Signed numerator/denominator pair; `1/2`, `2/4`, `0/2`, `0/0`, and `1/0` are distinct objects. |
| `float` | Python binary64 float. Signed zero is preserved; `bits:7ff8000000000042` specifies an exact NaN payload. |
| `date` | Gregorian `YYYY-MM-DD`, years 0001 through 9999. |
| `clock` | `HH:MM[:SS[.ffffff]]`, no timezone, hours 00 through 23. |
| `local` | Date and clock separated by `T`, without an offset. |
| `instant` | Timestamp with `Z` or an explicit `±HH:MM` offset; canonical output is UTC. |
| `duration` | Signed decimal elapsed seconds, optional `s`, exact to a microsecond. |
| `latlong` | `latitude,longitude` in decimal degrees, exact to 0.000001 degree. |
| `phone` | International `+` number of up to 15 digits, optional `;ext=004`; extension zeroes are preserved. |
| `ipv4`, `ipv6` | Full address domains; interface-scoped IPv6 is unsupported. |
| `uuid` | All 128 bits, without imposing version restrictions. |
| `semver` | Complete semantic version, including prerelease and build metadata; optional input `v`. |
| `isbn` | ISBN-10 or ISBN-13 with check digits; ISBN-13 begins 978 or 979. |
| `upc` | UPC-A, including the check digit and leading zeroes. |
| `chess` | Legal SAN/UCI sequence or PGN main line from the standard starting position; output uses UCI. |
| `go` | Legal Go sequence from an empty 19×19 (default), 9×9, or 13×13 board. |
| `tune` | Short monophonic melody and rhythm, using successive semitone steps and exact beat durations. |
| `list` | Ordered typed values, including nested lists. |

Clock, local time, timestamps, and durations use microseconds. Excess precision is
rejected, not rounded. Coordinates identify the two antimeridian spellings and
ignore longitude at either pole. Phone and retail-code validity is structural;
no assignment, ownership, or reachability checks are made.

Chess names preserve the move sequence, including unfinished games and the empty
game. PGN comments, headers, variations, and stated results are not named. Automatic
endings apply, including fivefold repetition and the 75-move rule; claimable draws
are not automatic endings. Moves are ordered lexically by UCI, independent of
library iteration order. Work is limited to 4096 plies per operation.

Go accepts coordinates with columns A through T, skipping I, rows counted from
the bottom, and `pass`. Black plays first. Use `9x9:D4 E4 pass pass` or
`13x13:J10`; an omitted size means 19×19. Canonical output always includes the
size. Captures apply before checking suicide, which is forbidden. Situational
superko forbids repeating a previous board with the same player to move; passes
are exempt, and two consecutive passes end the named play sequence. These move
legality conventions follow the [AGA rules](https://www.usgo-archive.org/files/pdf/conciserules.pdf).
Scoring, results, komi, handicap setups, SGF, and resumption after scoring are not
part of this format. Empty and unfinished sequences are supported, with a
4096-ply work limit. For example, `9x9:D4 E4 pass pass` has the name
`play:game:go:up trade real` with the default vocabulary.

Tunes use the `play:music:tune` prefix. For example:

```sh
nmr --operation encode --type tune --value '@1 2@1/2 r@1/3 -1@2/3'
# play:music:tune:have cycle tokyo
nmr --value 'play:music:tune:have cycle tokyo'
# @1 2@1/2 r@1/3 -1@2/3
```

The first note starts with `@duration`. Later steps are signed semitone differences
from the previous sounding note; omit a zero step. `r@duration` adds a rest.
Durations are exact beats, with reduced denominators containing powers of two and
at most one factor of three. Thus `1/6` is allowed, `1/9` is not, and `3/9` becomes
`1/3`. Transposition, playback tempo, and the center note do not change a name;
octave distances, beat scaling, and repeated attacks do. Adjacent rests merge,
trailing rests disappear, and a phrase must start with a sounding note.

In the browser, choose **Encode**, then `play:music:tune`. Load the example or
enter interval text, preview it, and edit note durations, pitch steps, and rests
in the rows. **Use notes** applies row edits. **Tie** joins contiguous same-pitch
notes; repeated attacks otherwise stay distinct. Decoded tunes also offer
playback. The default center is MIDI 60 (C4); another center transposes the sound.

Current codec work limits are 256 attacked notes, 20,000 text characters,
duration weight 512, and tune indices of 4,096 bits. A refusal reports a work
limit and never substitutes another tune. Browser previews allow 20–400 BPM,
MIDI pitches 0–127, at most 120 seconds, and notes at least 0.01 seconds long.
A tune can be named even when its preview is unavailable. Measured 4-, 8-, and
16-note motifs with the default vocabulary take 3, 8, and 16 payload words in
the examples in `plan/tunes.md`; these are measurements, not general bounds.

Prefixes remove type-routing overhead but cannot eliminate the information in
the value. A phone fits in four payload words in the example above.

## Your own vocabulary

Use a UTF-8 file with one word per line. Order matters. Empty lines and lines
beginning with `#` are ignored. Tokens cannot contain whitespace or `:`.
NFC normalization and Unicode case folding are the defaults; `--case-sensitive`
retains case. Duplicate normalized words are rejected. The same policy and
selected word count must be used by both people.

```sh
nmr --word-file private.txt --vocabulary-info
nmr --word-file private.txt --operation encode --type phone --value '+442079460958'
nmr --word-file private.txt --value 'data:contact:phone:YOUR WORDS HERE'
nmr --word-file private.txt --export-words normalized-private.txt
```

`--word-count N` selects the first N validated words. The default vocabulary uses
1,628 words. `--vocabulary-info` gives its SHA-256 identifier; a recipient can
require it with `--expect-vocabulary IDENTIFIER`. The identifier includes word
order and case policy. Export the normalized ordered list and share it through an
already trusted channel. The browser supports both file import and pasted lists.

A private vocabulary provides obscurity, not reliable encryption. Repeated values
produce repeated names; prefixes reveal types; a wrong vocabulary can produce a
plausible result. The vocabulary identifier detects a mismatch when supplied,
but does not authenticate the sender or the message. Verify important details.

Names never repeat a word, so a vocabulary has finite capacity:
`sum(W! / (W-k)!, k=1..W)`. Overflow produces an error; a larger vocabulary may be
needed. Many mistyped names are rejected, but another valid canonical name cannot
be distinguished from an intentional one without additional information.

## Browser tool

Build a mobile-friendly static tool from the installed core:

```sh
nmr --operation build-web --destination dist/web
python -m http.server 8765 --bind 127.0.0.1 --directory dist/web
```

Open `http://127.0.0.1:8765` locally, or host those files on an ordinary static
HTTPS server for friends. Direct `file:` loading does not support the worker and
asset loading used here. No conversion server or account is needed.

The page downloads pinned Pyodide 0.29.3 and its Pydantic packages. First load
requires a connection and a WebAssembly-capable modern browser. The project,
chess library, and semantic-version library are bundled from the same installation
that builds the site. Conversion runs in a worker; values and custom lists are
never sent over the network or saved in browser storage. Export a list explicitly
to retain it. Closing or reloading the page loses the in-memory list and inputs.

The WebAssembly bridge is tested in Node. Live browser interaction and visual
verification were blocked by the local browser approval gate during development;
`test/browser_smoke.cjs` and a manual CI job provide interaction checks to run where
browser access is available. No hosted deployment or PyPI publication was performed.

## Python library

```python
from nmr.nmr import Nmr
from nmr.types.fraction import Frac

engine = Nmr()
encoded = engine.encode("2/4", "frac")
assert encoded.name == "pure:math:frac:now"
assert engine.decode(encoded.name).value == "2/4"

explored = engine.decode("pure:to", browse=True)
assert engine.decode(explored.name).value == explored.value

fraction = Frac(numerator=2, denominator=4)
assert fraction.float() == 0.5
assert fraction.fraction().numerator == 1
```

`Frac` has no arithmetic or implicit numerical conversion. Its identity is the
stored pair. `.float()` returns infinities or NaN for zero denominators, and
otherwise delegates to the standard rational conversion; finite overflow raises
`OverflowError`. `.fraction()` returns `fractions.Fraction` and raises
`ZeroDivisionError` for zero denominators. Neither method changes the pair.
`Int` lives in `nmr.types.integer`; `Float` in `nmr.types.floating` stores exact
binary64 bits and exposes `.float()`.

Lists use explicit typed values rather than vocabulary-dependent names:

```json
[{"type":"date","value":"2000-02-29"},{"type":"phone","value":"+442079460958"}]
```

Encode that JSON with type `list`. Type names normalize to full paths; scalar
values must be strings. Nested lists use JSON arrays, not JSON encoded inside
strings. Lists preserve order. Limits are 256 items per list and eight nesting
levels; arbitrary browsing can encounter these work limits and is not promised
to succeed for every list index.

Integer tuples are ranked directly by total sum. For `n` nonnegative integers
with total `S`, preceding sum layers contain `comb(S + n - 1, n)` tuples; the
remaining offset is the rank of the tail tuple. For example, `(2, 1, 3)` has
rank 69. Inversion uses integer binomial comparisons and binary search. One-part
tuples are unchanged, and two-part tuples retain the Cantor pairing order.
List items share one tuple rank, and semantic versions pack major, minor, patch,
prerelease, and build indices as five components without nested pairing. The list
length is stored separately. This balances by sum, not by component bit length;
it does not guarantee a shorter name for every object.

## Format and development

The five root slots are `pure`, `real`, `data`, `play`, and the `list` leaf.
Every category has radix five. Below the root, slots 0–3 may hold leaves or
categories; slot 4 can only be empty or a category. The unnamed root alone is
exempt from the last-slot rule and cannot be nested. New types expand beneath
the four root categories. Published allocations never move, and leaves never
turn into categories.

List names use `list:` directly. An unprefixed list routes as `4 + 5 * payload`,
with one fewer routing step than the former `meta:list` path. Nested lists also
benefit from the shorter route; other type allocations are unchanged.

The exact allocations are in `nmr/registry.py`, using positional constructors
such as `Category("game", Chess, Go)`. Children are stored in an immutable tuple
of categories or codec classes. Tuple positions define the slots; unused slots
follow the last child. Categories require one to five children, with no `None`
entries or empty placeholder categories. Prefixes are ordinary paths
through that tree. At each edge, `parent_index = slot + 5 * child_index`.
A fuller prefix removes more of those routing components from the word payload.
`test/format.json` freezes shared Python and WebAssembly examples.

```sh
uv sync --frozen
uv run --frozen pytest
uv run --frozen ruff check --select B,E,F,I nmr test scripts
uv run --frozen ruff format --check nmr test scripts
uv run --frozen ty check nmr
uv run --frozen coverage run -m pytest
uv run --frozen coverage report
uv build
```

For WebAssembly checks, install `pyodide@0.29.3` in a temporary npm directory,
make it available through `NODE_PATH`, build `dist/web`, and run
`node test/runtime_smoke.cjs`. Browser interaction checks also need Playwright and
Chrome, or `NMR_BROWSER_CHANNEL=chromium` with Playwright's Chromium installed.
The workflow in `.github/workflows/check.yml` runs WebAssembly checks automatically
and offers browser interactions as a manual workflow-dispatch job.

See [the implementation plan](plan/nmr.md) for the contract, design rationale,
and resolved first-release decisions.
