# nmr

Find reversible truenames made from ordinary words for a birthday,
short tune, phone number, coordinate, fraction, identifier, or legal chess game,
then let a friend recover it with the same vocabulary.

A truename contains a readable type prefix and a payload without repeated words:

```text
date:mass nose
```

That truename means `2000-02-29`. Canonical decoding is the default. Browsing is an
explicit operation for discovering objects from other word combinations.

## Install and try

Requires Python 3.10 or newer and [uv](https://docs.astral.sh/uv/).
This checkout contains the new 1.0 format; it has not been published to PyPI.

```sh
git clone git@github.com:rec/nmr.git
cd nmr
uv sync --frozen
uv run --frozen nmr --operation encode --type date --value 2000-02-29
uv run --frozen nmr --value 'date:mass nose'
```

To install the CLI outside the checkout, run `uv tool install .`.
Use `nmr --help` for the complete options and `nmr --list-types` for type names.
Frozen development commands use the checked-in package versions independently of
machine-local resolution settings. Regenerate the lock deliberately when changing
dependencies.

## Encode, decode, and browse

```sh
# Preserve the actual fraction pair, including zero denominators.
nmr --operation encode --type frac --value '2/4'
# frac:who
nmr --value 'frac:who'
# 2/4

# The scope controls how much type information stays in the word payload.
nmr --operation encode --type chess --value 'e4 e5 Nf3'
# chess:in also
nmr --operation encode --type chess --value 'e4 e5 Nf3' --scope play
# play:most dana
nmr --operation encode --type chess --value 'e4 e5 Nf3' --scope ''
# rest cole

# Explore a noncanonical truename. The stable truename is printed to stderr.
nmr --operation browse --value 'pure:to'
# 0
# Canonical truename: pure:the

# One value per line; errors go to stderr and produce exit status 1.
printf '2000-02-29\n2024-12-31\n' | nmr --operation encode --type date

# JSON includes type, canonical value, truename, vocabulary ID, and canonical status.
nmr --operation encode --type phone --value '+442079460958' --json-output
```

Without `--value`, the CLI reads stdin, or prompts when used in a terminal.
`--value` preserves its entire argument, including whitespace, `#`, and newlines.
There is no implicit type guessing or country inference.

The convenience marker `name:` explicitly identifies a truename. It adds no
category or radix step: `name:the of` and `the of` have the same index, as do
`name:tune:the` and `tune:the`. Matching the marker ignores case. Use `--scope name`
to encode a full root truename with the marker. The browser shows only the full
root word sequence, without a prefix.

Category and type names are unique except for the `time` category and Time type.
Bare `time:` selects the type; `real:time:` selects the category containing Date,
Time, and Duration. Outputs use a single `time:` for the type and keep `real:time:`
when that category scope is needed. Parent categories
are optional in input: `chess:in also`, `game:chess:in also`, and
`:play:game:chess:in also` all read identically and print as `chess:in also`.
Category scopes behave the same way: `play:game:your land` prints as
`game:your land`, with the same payload. Results also use
short type labels. Internal tree paths still determine routing; shortening a
prefix never changes its scope or the encoded number.

Canonical decoding rejects unassigned type slots, invalid values, and
noncanonical encodings. It never silently switches to browsing. Browsing may
redirect those indices, returns a real supported object, and supplies its
canonical truename. Exploratory inputs can discover different objects as the tree
expands; save the canonical output instead.

## Supported details

| Type or path | Input and identity |
| --- | --- |
| `int` | Signed decimal integer, including very large integers within vocabulary capacity. |
| `frac` | Signed numerator/denominator pair; `1/2`, `2/4`, `0/2`, `0/0`, and `1/0` are distinct objects. |
| `float` | Python binary64 float. Signed zero is preserved; `bits:7ff8000000000042` specifies an exact NaN payload. |
| `date` | Gregorian `YYYY-MM-DD`, years 0001 through 9999. |
| `time` | `HH:MM[:SS[.ffffff]]`, no timezone, hours 00 through 23. |
| `duration` | Signed decimal elapsed seconds, optional `s`, exact to a microsecond. |
| `latlong` | `latitude,longitude` in decimal degrees, exact to 0.000001 degree. |
| `phone` | International `+` number of up to 15 digits, optional `;ext=004`; extension zeroes are preserved. |
| `ip` | IPv4 or IPv6 addresses, with a `use_ip6` family flag; interface scopes are unsupported. |
| `uuid` | All 128 bits, without imposing version restrictions. |
| `semver` | Complete semantic version, including prerelease and build metadata; optional input `v`. |
| `isbn` | ISBN-10 or ISBN-13 with check digits; ISBN-13 begins 978 or 979. |
| `upc` | UPC-A, including the check digit and leading zeroes. |
| `chess` | Legal SAN/UCI sequence or PGN main line from the standard starting position; output uses UCI. |
| `go` | Legal Go sequence from an empty 19×19 (default), 9×9, or 13×13 board. |
| `tune` | Short monophonic melody and rhythm, using successive semitone steps and exact beat durations. |
| `string` | Unicode text, preserving case and allowed spaces; excludes U+0000–001F, U+007F–009F, and surrogates. The empty string is supported. No Unicode normalization is applied. |

String character indices count `a`–`z`, then `A`–`Z`, then the remaining allowed
U+0020–00FF characters in code-point order, then higher Unicode scalar values.
Character tuples use the shared diagonal enumeration by total sum; the length
is encoded with a trailing-binary length tag. For example,
`dfasdfasdf` is `string:she dump stan learn river`. Browsing wraps character
indices outside the alphabet and repairs noncanonical empty-string indices.

Time of day and durations use microseconds. Excess precision is
rejected, not rounded. Coordinates identify the two antimeridian spellings and
ignore longitude at either pole. Phone and retail-code validity is structural;
no assignment, ownership, or reachability checks are made.

Formatted phone input is normalized with `phonenumberslite`, using international
E.164 digits plus our `;ext=digits` suffix. For example,
`+44 (0)20 7946 0958 ext. 004` becomes `+442079460958;ext=004`. The library
handles national trunk prefixes, significant leading zeroes, Unicode digits,
and vanity letters. Review the normalized result before sharing its truename.
An explicit `+` country code is still required; nmr does not guess a region.
Already canonical `+digits` values are literal identifiers, including unassigned
or short values, so established truenames do not depend on changing library metadata.
This is input normalization, not a check that a number is assigned or reachable.

Chess truenames preserve the move sequence, including unfinished games and the empty
game. PGN comments, headers, variations, and stated results are not included in the truename. Automatic
endings apply, including fivefold repetition and the 75-move rule; claimable draws
are not automatic endings. Moves are ordered lexically by UCI, independent of
library iteration order. Work is limited to 4096 plies per operation.

Go accepts coordinates with columns A through T, skipping I, rows counted from
the bottom, and `pass`. Black plays first. Use `9x9:D4 E4 pass pass` or
`13x13:J10`; an omitted size means 19×19. Canonical output always includes the
size. Captures apply before checking suicide, which is forbidden. Situational
superko forbids repeating a previous board with the same player to move; passes
are exempt, and two consecutive passes end the encoded play sequence. These move
legality conventions follow the [AGA rules](https://www.usgo-archive.org/files/pdf/conciserules.pdf).
Scoring, results, komi, handicap setups, SGF, and resumption after scoring are not
part of this format. Empty and unfinished sequences are supported, with a
4096-ply work limit. For example, `9x9:D4 E4 pass pass` has the truename
`go:site color map` with the default vocabulary.

Tunes use the `tune` prefix. For example:

```sh
nmr --operation encode --type tune --value '@1 2@1/2 r@1/3 -1@2/3'
# tune:open giant sale table
nmr --value 'tune:open giant sale table'
# @1 2@1/2 r@1/3 -1@2/3
```

The first note starts with `@duration`. Later steps are signed semitone differences
from the previous sounding note; omit a zero step. `r@duration` adds a rest.
Durations are exact beats, with reduced denominators containing powers of two and
at most one factor of three. Thus `1/6` is allowed, `1/9` is not, and `3/9` becomes
`1/3`. Transposition, playback tempo, and the center note do not change a truename;
octave distances, beat scaling, and repeated attacks do. Adjacent rests merge,
trailing rests disappear, and a phrase must start with a sounding note.

In the browser, type interval text directly into the single field to find a tune's
truename. The result plays the tune of its full root index. Entering a truename
instead displays the browsed object. For a `tune:` truename, the object line
contains the interval notation and plays the original melody. The library's
`Nmr.to_tune()` supports both prefix-relative and absolute interpretations.
Browser playback runs at 180 BPM, centered on F3 (MIDI 53), rather than
starting there. Click the truename again while it plays to stop it.

Tunes are ordered by total complexity: one per attack, no extra pitch cost for
steps from -2 through +2 semitones, and `abs(step)-2` for larger steps,
duration weight `4h+a+3b`, and one plus duration weight for positive gaps. More
simple notes compete with fewer complicated ones. Exact rational generating
functions count all layers and completions; there is no separate length header.
The six weights and free-step radius are centralized in `nmr/types/tune_count.py` for design changes
before release. They are not runtime switches: changing them changes truenames.

Current codec work limits are 256 attacked notes, 20,000 text characters,
duration weight 512, total complexity 4,096, and tune indices of 4,096 bits.
A refusal reports a work limit and never substitutes another tune. Browser previews allow 20–400 BPM,
MIDI pitches 0–127, at most 120 seconds, and notes at least 0.01 seconds long.
A tune can receive a truename even when its preview is unavailable. Measured 4-, 8-, and
16-note motifs with the default vocabulary take 4, 10, and 19 payload words in
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
nmr --word-file private.txt --value 'phone:YOUR WORDS HERE'
nmr --word-file private.txt --export-words normalized-private.txt
```

`--word-count N` selects the first N validated words. The default vocabulary uses
1,628 words. `--vocabulary-info` gives its SHA-256 identifier; a recipient can
require it with `--expect-vocabulary IDENTIFIER`. The identifier includes word
order and case policy. Export the normalized ordered list and share it through an
already trusted channel. Custom vocabulary tools are available through the CLI
and Python library; the minimal browser uses the default vocabulary.

A private vocabulary provides obscurity, not reliable encryption. Repeated values
produce repeated truenames; prefixes reveal types; a wrong vocabulary can produce a
plausible result. The vocabulary identifier detects a mismatch when supplied,
but does not authenticate the sender or the message. Verify important details.

Truenames never repeat a word, so a vocabulary has finite capacity:
`sum(W! / (W-k)!, k=1..W)`. Overflow produces an error; a larger vocabulary may be
needed. Many mistyped truenames are rejected, but another valid canonical truename cannot
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

To build and deploy to `https://ax.to/nmr`, run from the checkout:

```sh
uv run --frozen python script/deploy.py
```

This uses your SSH keys for `root@ax.to`, uploads changed files with rsync to
`/home/ax/public_html/nmr/`, and sets the deployed directory and all its contents
to owner `ax` and group `ax`. Files already on the server are not deleted.
The deployment sets the asset base to `/nmr/` and includes `.htaccess`: Apache
serves `/nmr` directly and redirects `/nmr/` to `/nmr`, preserving the query.
Apache 2.4 must enable `mod_rewrite` and allow the `FileInfo`, `Indexes`, and
`Options` override classes for this directory. Local builds retain relative assets.

The page downloads pinned Pyodide 0.29.3 and its Pydantic packages. First load
requires a connection and a WebAssembly-capable modern browser. The project,
chess library, and semantic-version library are bundled from the same installation
that builds the site. Conversion runs locally in a worker. Each text edit updates
`desc` or `name` in the current URL without a network request or an extra browser history entry.
Copy or bookmark that URL to share the query; opening it fills the field and runs
recognition. Spaces appear as `+`, and literal plus signs and other special
characters are escaped. For example: `/nmr?desc=Tom+Ritchford`.

The query is part of the shared URL and is sent to the hosting server when that
URL is opened or reloaded. The app does not save the input in local storage.

The page has two panes beneath the `nmr` heading: description and true name.
The left pane is always editable. Swap exchanges the captions and moves the first
converted result into the editor. With no result, it starts with an empty editor.
URLs contain exactly one parameter: `desc` for description mode or `name` for
true name mode, including when the field is empty. Opening a link restores both
the text and direction. A URL without either starts with an empty description.

In description mode, the engine recognizes integers, explicit `+` phone numbers,
fractions, ISO dates and times, coordinates, IP addresses, UUIDs, versions,
durations, chess/Go moves, and tune notation. Pure digits mean an
integer; slash pairs mean fractions. Use `YYYY-MM-DD` for dates. Other text,
including vocabulary words such as `Tom`, becomes a String with its original case
and spaces. Incomplete type syntax waits for more input; invalid typed values
remain errors. Type labels can make a description explicit, such as
`upc: 036000291452` or `string: "123"`. Strings in typed descriptions use JSON
quoting so swapping preserves their type, quotes, and whitespace.

In true name mode, accepted text is followed by a grey suggested continuation.
Completed words must be distinct vocabulary words; the current fragment must
match an unused word's beginning. Suggestions are chosen randomly. Only lowercase
letters and Space enter text; impossible letters and other editing keys make a
quiet 20 ms F3 tick instead. Space accepts the selected suggestion. Right accepts
at least one letter, continuing through unambiguous characters. Completing the
selected word inserts a space and suggests an unused next word. Left and Backspace
move back to the previous character choice, skipping forced stretches and removing
an automatic space when needed. For example, `axis ` returns to `a`.
Up/Down cycle through matching continuations or eligible next words. Clicking and
selection cannot move this cursor. Text remains selectable and copyable with the
mouse and the usual copy shortcut or context menu. Tab still navigates the page controls.

The right pane uses browsing to decode completed, accepted words only. Partial
words and guesses do not change or hide the description. Completing a word accepts
it and updates the description. Type
prefixes from swaps and bookmarks stay fixed before the controlled word sequence.
Swapping or loading a bookmark accepts complete words and normalizes their case.

Click the result on the right to play its tune. description mode shows the full
root truename without a prefix and plays its full root tune. true name mode
shows the browsed object's description and plays its prefix-relative tune.
Click the playing result to stop. In description mode, Enter also plays the result.

In description mode, type anywhere on the page; click the field to position its cursor, drag to select,
or double-click to select a word. Arrow keys, Home/End, Shift selection,
copy/cut/paste, and insertion in the middle work normally. Escape clears the field
and stops playback. Phone input containing `+` and digits rejects typed letters
with a quiet tick. Clear or replace the whole field to enter a different detail.
The String codec rejects control ranges U+0000–001F, U+007F–009F, and surrogate
code points.

The opening sound is `tune:the` itself, a one-beat F3 at 180 BPM. Browsers that block autoplay
will play it on the first interaction instead. Work and playback limits still apply.

The Clock page at `/nmr/clock` shows local time as `HH:MM:SS` and updates its
truename every second. Sound starts off and is enabled with **On**. Choose
5 seconds, 10 seconds (the default), 1 minute, or 60 minutes. Playback starts
on matching wall-clock boundaries, such as `:00`, `:10`, …, `:50` for 10 seconds,
or the top of each hour for 60 minutes. Changing the interval waits for the next
matching boundary. Tunes continue playing while muted; the On checkbox fades
the output in or out over 100 ms without restarting the tune. It uses the same time
codec and prefix-relative tune as the main page, with F3 at 180 BPM.

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
assert encoded.truename == "frac:who"
assert engine.decode(encoded.truename).value == "2/4"

explored = engine.decode("pure:to", browse=True)
assert engine.decode(explored.truename).value == explored.value

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

Integer tuples are ranked directly by total sum. For `n` nonnegative integers
with total `S`, preceding sum layers contain `comb(S + n - 1, n)` tuples; the
remaining offset is the rank of the tail tuple. For example, `(2, 1, 3)` has
rank 69. Inversion uses integer binomial comparisons and binary search. One-part
tuples are unchanged, and two-part tuples retain the Cantor pairing order.
Semantic versions pack major, minor, patch, prerelease, and build indices as five
components without nested pairing. This balances by sum, not by component bit
length; it does not guarantee a shorter truename for every object.

## Format and development

The four root slots are `pure`, `real`, `data`, and `play`. Every category has
radix four. Slots 0–2 may hold leaves or categories; slot 3 can only be empty or a
category. This rule applies at every depth, including the root. The unnamed root
cannot be nested. Published allocations never move, and leaves never turn into
categories.

The exact allocations are in `nmr/registry.py`, using positional constructors
such as `Category("game", Chess, Go)`. Children are stored in an immutable tuple
of categories or codec classes. Tuple positions define the slots; unused slots
follow the last child. Categories require one to four children, with no `None`
entries or empty placeholder categories. Prefixes are ordinary paths
through that tree. At each edge, `parent_index = slot + 4 * child_index`.
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
