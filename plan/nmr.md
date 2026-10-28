# nmr: plan for a useful first release

## Purpose and scope

Give people a practical way to turn their important details into short, reproducible
truenames, share those truenames, and let friends recover the original details easily.
Keep the more playful ambition: a short truename can also discover an interesting,
valid object, including a legal chess game.

The user subsequently authorized autonomous implementation of this whole plan,
including architectural changes and replacement of all pre-release mappings.
The implementation slices are complete in the repository. The final section
records the defaults chosen for the original open questions. Hosting and package
publication have not been performed; live browser approval remains unavailable.

Additional work beyond the prompt: None.

### Decisions established in discussion

* Existing truenames occur only in this project's unit tests. There are no external
  truenames to preserve; revise those fixtures deliberately when establishing the format.
* Once established, canonical truenames must remain backward compatible forever.
  There is no later incompatible format reset. Adding types must remain possible
  without changing the meaning of any existing canonical truename.
* The root slots, in order, are `pure`, `real`, `data`, and `play`. Every category
  node has four slots, with fixed radix four. List is not a supported type.
* The last slot, index 3, may be empty or contain a category, never a leaf.
  Slots 0 through 2 may be empty, leaves, or categories. This rule applies at
  every depth, including the root; expansion uses ordinary categories.
* Canonical decoding is the default. Browsing is a separate, explicit operation
  that can map unassigned or out-of-range indices into supported choices.
* The namable numeric classes are `Int`, `Frac`, and `Float`.
* `Frac` preserves an ordered pair of arbitrary signed integers, including zero
  denominators. It is not a numerical class. Numerical work belongs to existing
  classes obtained through `.float()` and `.fraction()`.

The release should provide:

* A dependable Python library and command-line tool.
* A small, mobile-friendly browser encoder/decoder that friends can use without
  installing Python, registering, or uploading their private details.
* Useful codecs for the supported personal details, numbers, and games.
* Optional hierarchical prefixes that reveal the type and reduce the integer
  encoded by the word payload, using the same permanent numeration in every scope.
* Straightforward custom-word-list creation, loading, and sharing.
* Explicit guarantees about canonical truenames, losslessness, completeness, capacity,
  and the limits of privacy.

Do not include accounts, cloud storage, social features, native mobile apps,
contact synchronization, or a general plugin marketplace in this release. Music,
chemistry, and additional board games remain outside the release unless chosen
to replace another scoped feature.

## Initial repository assessment

This is the historical assessment that informed the repair work. These paths and
defects describe the starting point, not the current implementation.

`Words` ranks and unranks sequences without repeated words using a configurable,
ordered vocabulary. `TypeNamer` maps values to nonnegative integers, and
`category.py` packs group and subtype identifiers into a global integer. `Nmr`
joins these operations. There are useful round-trip and word-stability tests.

The default vocabulary uses 1,628 words. The six-word capacity claim concerns
raw 64-bit integers; adding type information can require additional words.

The ordinary registry currently imports integers, fractions, IPv4, IPv6,
coordinates, UUIDs, and semantic versions. Chess has a separate implementation
and tests, but is not imported by the ordinary registry. Time and phone-number
modules are unfinished. Declaring a category does not mean its codec exists.

### Repair inventory

| Area | Observed issue | Required outcome |
| --- | --- | --- |
| Integer packing | `Packer` uses floating-point square root to invert Cantor pairing. | Exact integer arithmetic, including large indices and pairing boundaries. |
| Fractions | `fractions.Fraction` reduces pairs, rejects zero denominators, and the codec collapses zero numerators. | Replace the truename representation with `Frac`; preserve both signed integers exactly, including `0/0`. |
| Type selection | `get_class` refers to an undefined variable and builds its lookup from metaclass truenames; parsing catches every exception. | Deterministic type lookup; expected parse failures separated from programming errors; explicit ambiguity handling. |
| Registration | Import order controls availability, and reserved categories can reach missing codecs. | One deliberate supported-type registry; independent of test import order; unsupported slots handled according to the chosen completeness contract. |
| Coordinates | Longitude formatting modifies latitude; latitude endpoints are conflated; precision documentation disagrees with the scale. | Correct hemispheres and boundaries, defined coordinate equivalence, explicit resolution, and no silent precision loss. |
| Semantic versions | Prerelease and build metadata are parsed but discarded during encoding. | Preserve the complete supported version or reject unsupported forms before encoding. |
| Time | Duplicate class definitions, undefined truenames, mismatched constants, incomplete decoders, approximate calculations. | Replace the unfinished implementation with the agreed, exact date/time codecs. |
| Phone numbers | Duplicate definitions and copied semantic-version code. | A working, clearly bounded phone codec. |
| Chess | Encodes FEN fields; arbitrary decoded fields need not form a legal position, and positions do not preserve a game's moves. | Separate the promised object and legality guarantee before choosing its enumeration. |
| CLI | Disabled tests, unused options, disconnected random generation, ignored stored error status, and argument quoting that can alter input. | A coherent, tested command interface, faithful input handling, and meaningful exit codes. |
| Words | Empty input, repetition, token syntax, and normalization are not a consistent public contract. | One documented grammar enforced across library, CLI, and browser. |
| Packaging/docs | Word file is located outside the package; README/API examples are stale; time tests contain no cases. | Verify installed wheels and source distributions, bundle the vocabulary reliably, and publish executable examples. |

The old category implementation was replaced under the subsequent architectural
authorization. Unimplemented card games remain outside the first-release scope.
Unrelated `TAGS` and `reflog.txt` files were left untouched.

## Define the format before adding codecs

### Canonical values and truenames

For the permanent format, a fixed ordered vocabulary, and a prefix scope:

1. Every supported canonical value has exactly one canonical truename within capacity.
2. Canonically decoding that truename recovers the same typed canonical value.
3. Different canonical values of the same type never share a canonical truename.
4. Different prefixes may give different truenames for the same typed value.
5. Canonical decoding rejects every truename outside the image of canonical encoding.
6. Browsing may accept a noncanonical truename and return an object with a different
   canonical truename. This does not make the original input a canonical truename.

Canonical encoding is an injection from the supported target objects into the
truename space. Canonical decoding is its partial inverse. That image can be sparse;
many well-formed truenames need not encode anything canonically. Density depends on the
codec: an integer-pair enumeration can fill its leaf space without requiring
every other codec to do so.

After resolving the exact allocation and decoding the object, verify canonical
membership by re-encoding under the same prefix and vocabulary. Compare the
normalized truename tokens under the documented lexical rules. Reject reserved slots,
invalid objects, and noncanonical indices; never silently fall back to browsing.

Distinguish value preservation from spelling preservation. For example, equivalent
IPv6 spellings may have one canonical output; a phone identifier must retain
meaningful leading zeroes. Display normalization before encoding whenever the
input spelling will change. Do not
round, truncate, infer a country, or discard timezone information silently.

An object's identity is defined by its type, not universally by numerical equality.
In particular, `Frac(1, 2)` and `Frac(2, 4)` are distinct objects and get distinct
canonical truenames even though converting them to rational values gives equal results.

The existing category table, codec mappings, and default vocabulary can be revised
now because only local tests use them. Establish final allocations and fixtures
before release; do not build a legacy decoder for the abandoned mappings. After
that point, allocations, vocabulary order, normalization, and canonical codec
semantics must remain stable forever. Extensions may fill reserved space but may
not reinterpret an existing canonical truename. Changes to browsing results do not
weaken this guarantee. No future version switch is an escape from it.

### Permanent, extensible type allocation

Use fixed branching of four at every category node, including the root. Replace
the separate radix override table with this uniform rule. It governs type routing,
not the internal enumeration of objects within a leaf codec.

The root allocation is settled:

| Slot | Category or leaf | Scope |
| --- | --- | --- |
| 0 | `pure` | Math and science. |
| 1 | `real` | Time and geographic location, including latitude/longitude. |
| 2 | `data` | Computing, communication, contacts, and identifiers. |
| 3 | `play` | Art, music, and games. |

`pure` is the category name; “canonical” refers to encoding and decoding,
not a category. Place the existing mathematical and scientific types under
`pure`; time and coordinates under `real`; addresses, registered values, and
identifiers under `data`; and art and games under `play`. Exact subcategory names, slot
assignments and structural leaves are now explicit in `nmr/registry.py`:

| Category path | Occupied child slots |
| --- | --- |
| `pure` | 0: `math` (category). |
| `pure:math` | 0: `int`, 1: `frac`, 2: `float`. |
| `real` | 0: `time` (category), 1: `latlong`. |
| `real:time` | 0: `date`, 1: `time` (Time type), 2: `duration`. |
| `data` | 0: `address`, 1: `register`, 2: `id` (categories). |
| `data:address` | 0: `ip`, 1: `phone`. |
| `data:register` | 0: `isbn`, 1: `upc`; values backed by an external registry. |
| `data:id` | 0: `uuid`, 1: `semver`, 2: `string`. |
| `play` | 0: `game`, 1: `music` (categories). |
| `play:game` | 0: `chess`, 1: `go`. |
| `play:music` | 0: `tune`. |

The category `real:time` and its Time leaf `real:time:time` deliberately share
`time`. Bare `time:` always selects the leaf. Category-scoped names retain
`real:time:` so they cannot be confused with leaf payloads. Qualified Time paths
normalize to one `time:` prefix; other category and type labels remain unique.

All unlisted slots are empty. Science, art, and additional games retain
their agreed conceptual homes but do not acquire placeholder leaf allocations.

Finding truenames for short tunes is nmr's original motivating purpose. `plan/tunes.md` defines
the implemented combined melody/rhythm profile, transposition equivalence, and
centered playback presentation.

Represent the hierarchy with `Category(truename, *children)`, storing children as
`tuple[Category | type[TypeNamer], ...]`. Tuple order assigns slots without an
integer-keyed dictionary. Every category has one to four children; entries cannot
be `None`, and unused slots follow the final child. This representation preserves
the numbered ordering of its children.

At every level, slots 0 through 2 may hold a specifically defined leaf type or
a category. Slot 3 may be empty or a category, but must never be a leaf. The
unnamed root follows the same restriction and cannot be nested. Its four children
are `pure`, `real`, `data`, and `play`.

To extend a full category, descend through slot 3. If that slot is empty, create
a category there and place the new type in an available slot 0 through 2 beneath
it. In a finite tree, repeatedly following slot 3 eventually reaches an empty
slot, so space for extension always exists. Other slots can also contain
categories. This guarantees structural room, not a semantically appropriate home
for every type: choose category meanings with their descendants in mind.

Published slots and category paths never move. A published leaf never becomes a
category, and an occupied category never becomes a leaf. Never resize a node or
derive its radix from the current number of implemented children. Every branch
is an ordinary named category and contributes to the visible prefix path.

For a slot `s` and remaining payload integer `n`, routing is `s + 5*n`; decoding
uses division with remainder by five. Each additional category edge adds a radix
step. The word-permutation ranking remains unchanged. Measure actual truename lengths
and prefix savings using this layout. Finite vocabulary capacity still bounds
which particular objects can be expressed with a particular list.

Unassigned slots are invalid in canonical decoding. Browsing may redirect them
to supported children. When an unassigned slot is later populated, its browsing
result may change, but no previously canonical truename changes meaning. Never
redirect an already canonical input.

### Hierarchical prefixes

Use a category or type name followed by a colon and a word payload.
Category and type labels are globally unique except for the `time` category and
Time type; a registry unit test enforces this exact exception. Bare `time:` means
the Time type; `real:time:` means its category. Parent categories may be supplied
on input, including an optional leading colon. Output prints the shortest prefix
that preserves the selected scope, keeping `real:time:` for the category. Thus `:play:game:chess:in also` prints as `chess:in also`.

* No prefix: words encode the global integer.
* `name:`: a convenience marker with no category, slot, or radix cost. It is
  removed before interpreting the remaining truename, so it can also wrap an
  existing category/type prefix. The browser uses it to mark displayed truenames.
* `play:`: words encode the integer inside the play category.
* `game:`: words encode the integer inside the game category.
* `chess:`: words encode the integer inside the chess leaf.

For that illustrative path, let `g` be the game slot within `play`, `c` the chess
slot within `game`, and `n` the type-relative integer. The global integer is:

`I = 3 + 4 * (g + 4 * (c + 4*n))`

The payload integers for no prefix, `play:`, `game:`, and
`chess:` are respectively `I`, `g + 4*(c + 4*n)`, `c + 4*n`, and `n`.
The values of `g` and `c` are not assigned by this example. Decoding a prefix
restores the omitted fixed routing components. This preserves the type-relative
integer and makes the forms equivalent without changing the word-ranking algorithm.

Keep prefixes outside the vocabulary. A custom list changes the payload words,
not the spelling or meaning of the category path. A prefix restricts decoding to
its scope; it must never be treated as a hint that the decoder can ignore. Remove a
prefix only by decoding and re-encoding, never by deleting its text.

Use exact, documented prefix truenames, normalized consistently across clients. Do
not initially add abbreviations or synonyms. Reject unknown paths, missing
payloads, and extra path components with useful errors. Explicit encode/decode
operations must distinguish a prefixed truename from raw values containing colons,
such as IPv6, timestamps, or URLs.

Recommend the most specific prefix as the default output, with an explicit
selection for a broader or unprefixed scope. A narrower scope cannot increase
the canonical payload word count for the same type-relative integer, but the
prefix may make the whole printed truename longer. Show actual counts rather than
promise a fixed saving.

The example `they see what they may` repeats `they`, contrary to the existing
nonrepetition rule. Treat the supplied examples as illustrations of scope, not
valid equivalence fixtures. Recommended policy: retain nonrepetition and replace
them with generated, verified examples. Whether repeated words should become
accepted browsing input is a question for the format decision.

### Browsing and completeness

Browsing follows the same hierarchy as canonical decoding, but when an index
selects an unfilled box or lies outside a supported domain, it chooses an index
inside the supported choices. Define the choice deterministically, for example
by modulo over an explicitly ordered set of available children. Never depend on
import order, randomness, or machine-local state. Share the parsing and ranking
machinery; keep the decision to redirect explicit.

Browsing must agree with canonical decoding on every canonical input. For other
inputs it returns the discovered typed object and that object's canonical truename
under the selected scope and vocabulary. Save or share that canonical output,
not the exploratory input. If it cannot be represented under the selected scope
and vocabulary, report capacity failure rather than claiming a usable discovery;
exclude such inputs from any promised complete browsing range.

Only canonical meanings are permanent. Browsing results can change as new children
are filled in or browsing rules improve. Make this distinction visible in the API,
CLI, browser, and documentation; never silently browse after canonical decoding
fails. Prefix restrictions apply in both modes.

Completeness is a browsing guarantee: every syntactically valid payload inside a
published range produces an object satisfying the type's validity rules and a
representable canonical truename. Canonical decoding is intentionally partial.
Wrapping routing indices alone cannot make an invalid object legal; each codec
must supply a valid construction or a defined domain mapping.

### Capacity and browsing guarantees

For a vocabulary of size `W`, the number of nonempty, nonrepeating payloads of
at most `k` words is:

`C(W, k) = sum(W! / (W-j)!, j=1..min(k, W))`

Those truenames represent indices `0 <= n < C(W, k)`. With all lengths allowed, the
space contains `W!` full-length permutations plus all shorter permutations. At
1,600-plus words it is enormous. Keep accurate capacity checks, especially for
small custom lists; never silently discard data on overflow.

Publish completeness per scope and codec, with a bound expressed as an index
range and the corresponding word lengths for the chosen vocabulary. Distinguish:

* Exact canonical round-trip support for values inside capacity.
* Total browsing of all payload indices inside the promised bound.
* Syntactic validity, semantic validity, and externally verifiable facts.

For finite dense types, canonical indices cover the finite domain. Browsing can
map higher indices into that domain through a documented modulo rule. For
structured types, rank valid objects directly where practical. Do not promise
completeness through searching until something happens to be valid.

For a group or global browsing scope, every advertised input must reach a supported
codec. Document how empty slots and categories without implemented
children are redirected within the prefix scope. Publish complete leaf ranges
first and broader ranges where that construction is established. Unlike canonical
allocations, these browsing redirects do not reserve permanent aliases.

Always show the canonical truename after browsing. Canonical decoding rejects truenames
outside the canonical image, which catches some mistakes, but a mistyped truename can
still be another canonical truename. Neither mode authenticates the sender or proves
that the decoded object is the intended one.

## First-release type coverage

“All common types” needs a finite release definition. The following is the proposed
coverage. Generic strings are outside this scope. Allocate leaves through the
chosen permanent expansion mechanism.

| Type | First-release scope and canonicalization | Browsing completeness target |
| --- | --- | --- |
| `Int` | Signed arbitrary-size integers, limited by vocabulary capacity. | Every payload index. |
| `Frac` | Ordered pairs of arbitrary signed integers, including zero denominators; preserve the pair exactly. | Every payload index through exact signed-integer encoding and pairing. |
| `Float` | Exact Python binary64 bits, including signed zero, infinity, NaN signs and payloads. `bits:HEX` supplies an exact pattern. | Full 64-bit domain; higher indices wrap only when browsing. |
| Dates | Gregorian calendar dates, including birthdays; recommend years 1 through 9999 initially. | Dense day enumeration; browsing redirects beyond the finite range. |
| Time | Time of day without a date or timezone, at microsecond resolution. | Dense microseconds within a day; browsing wraps beyond the domain. |
| DateTime | Date and Time combined as `date_index * 86_400_000_000 + time_index`, without a timezone. Time is the least significant component. Canonical text uses `YYYY-MM-DDTHH:MM:SS[.ffffff]`. | Dense microseconds across years 0001 through 9999; browsing wraps beyond the domain. |
| Phone numbers | International numbers with explicit country calling code and optional extension. Normalize formatted input with `phonenumberslite` to E.164 digits and `;ext=digits`; retain significant zeroes. Already canonical digits remain literal and metadata-independent. No implicit regional parsing. | No assignment or reachability check; decoded identities do not depend on numbering-plan metadata. |
| Coordinates | Latitude/longitude at a declared fixed resolution, with poles and antimeridian equivalence specified. | Every canonical grid point; browsing redirects under documented rules. |
| IP addresses | One IP class with a `use_ip6` boolean; canonical standard spelling. The index is twice the address integer plus its family flag. Scoped IPv6 is unsupported. | Full address domains, including non-routable addresses. |
| UUIDs | Preserve all 128 bits; do not invent UUID-version constraints. | Full 128-bit domain. |
| Semantic versions | Major, minor, patch, prerelease, and build metadata. | Browsing repairs empty metadata identifiers and numeric prerelease leading zeroes; canonical decoding rejects invalid indices. Capacity still applies to the repaired output. |
| ISBN and UPC | Checked ISBN-10, ISBN-13 with 978/979 prefix, and UPC-A; no assignment claims. | Dense finite domains, with browsing-only wrapping. |
| Chess | A legal move sequence from the standard initial position, including unfinished and empty games. | Every payload index whose decoding stays within the 4096-ply work limit and whose canonical truename fits. |
| Go | Alternating moves from an empty 19×19, 9×9, or 13×13 board, including empty and unfinished games. Captures, no suicide, situational superko; two passes end play. | Every payload index whose decoding stays within the 4096-ply work limit and whose canonical truename fits. |

ISBN and UPC have compact checked codecs. There are no ownership, delivery,
assignment, or account-existence checks.

Measure realistic output lengths for every proposed use case. If common details
produce impractically long truenames, revise the release scope or representation
before describing the product as easy to share. Do not add compression or contact
bundles without a demonstrated need and an explicit decision.

### `Int`, `Frac`, and `Float`

Use these exact truenames for the namable numeric classes. Reuse existing numerical
classes for numerical operations; do not implement a new arithmetic system.
`Float` stores binary64 bits and returns the standard Python float through
`.float()`. NaN spelling is `bits:HEX` to preserve payload and sign. There is no
separate decimal codec in this release; an exact decimal value can be represented
as a numerator/denominator pair.

`Frac` stores a numerator and denominator as signed integers. Its identity is the
ordered pair: `1/2`, `2/4`, and `50/100` are different fractions; so are `0/2` and
`0/3`, or `1/-2` and `-1/2`. Zero denominators are allowed, including `0/0`.
Do not cancel factors, move signs between components, or special-case all zero
numerators into one object. Lexical variations such as surrounding whitespace
need not be part of that identity.

Encode each signed component using the integer enumeration, then pair the two
nonnegative indices exactly. Decode the pair by reversing those operations. The
encoded object must never pass through `fractions.Fraction` during that round trip.

Expose two explicit numerical conversions:

* `.float() -> float`: for a nonzero denominator, delegate numerical conversion
  to existing Python numerical facilities. For denominator zero, return positive
  infinity for a positive numerator, negative infinity for a negative numerator,
  and NaN for `0/0`. Do not mutate the stored pair. Finite-value overflow follows
  the standard rational conversion and raises `OverflowError`.
* `.fraction() -> fractions.Fraction`: construct the standard-library rational
  from the pair. It may reduce factors or normalize denominator signs in the
  returned value; the original `Frac` remains unchanged. A zero denominator cannot
  be represented by `fractions.Fraction`; propagate its `ZeroDivisionError`
  rather than inventing a special rational object or returning a different type.

`Frac` otherwise does not act like a number: no arithmetic, ordering, equality
against numerical values, or implicit numeric conversion protocols. Ordinary
object equality compares the stored pair. Callers explicitly convert before
doing numerical work. In particular, do not implement the previously discussed
extended-fraction arithmetic or numerical equality between different pairs.

## Chess: legal games and positions

The existing code truenames FEN positions, not games. A valid FEN structure does not
prove that a position is reachable from the standard starting position. A game
also includes its move sequence; several games can lead to the same position.

The implemented first-release object is a finite sequence of legal moves from the
standard initial position, including an unfinished game. Accept a simple move
sequence or PGN main line; explain that comments, variations, and headers are not
part of the encoded object unless separately included in the agreed scope.

A concrete complete enumeration is the rooted tree of legal games:

1. Index zero denotes the current move sequence ending here, including the empty
   sequence at the initial position.
2. At a nonterminal position, order legal moves by a frozen, documented move
   notation, not by library iteration order.
3. For positive index `n`, divide `n-1` by the number of legal moves. The remainder
   selects a move and the quotient continues from the resulting position.
4. At a terminal position, canonical decoding requires the remaining index to be
   zero. Browsing may map a remaining positive index to the sequence ending there,
   then return that sequence's canonical truename.

This constructs reachable games directly and supports inverse ranking without
enumerating all positions. Freeze automatic termination rules, including draws,
and distinguish claimable draws from automatic endings. Measure work for extreme
indices before publishing a word-length guarantee; enforce limits before decoding,
not after silently truncating the game.

The chess leaf truenames a game, not a FEN position. Move ordering is lexical UCI.
Automatic game endings include fivefold repetition and the 75-move rule; claimable
draws do not force termination. Both encoding and decoding enforce a 4096-ply work
limit. PGN headers, comments, variations, and results are not part of the object.

### Go

The requested Go extension occupies previously empty `play:game` slot 1. No
existing allocation or canonical truename changes. The value is a move sequence
starting with Black on an empty board. Input optionally begins `19x19:`, `9x9:`,
or `13x13:`; the default is 19×19, and canonical output always includes the size.
Coordinates use columns `ABCDEFGHJKLMNOPQRST`, with row 1 at the bottom, plus
`pass`. Input coordinates and passes are case-insensitive.

Freeze board-size tags as 19×19 = 0, 9×9 = 1, and 13×13 = 2. The leaf index is
`tag + 3 * sequence_rank`; this three-size domain is permanent. Moves are ordered
by row then column (`A1`, `B1`, ..., `A2`, ...), with pass last. Sequence ranking
uses the chess stop-or-legal-child recurrence above. Captures remove whole
connected opposing groups without liberties before checking the played group.
Suicide is illegal. Situational superko rejects a stone move that recreates an
earlier board and next-player combination, including the initial empty board.
Passes are exempt from repetition checks, recorded in history, and two consecutive
passes terminate the encoded sequence. These move legality rules follow the
[AGA concise rules](https://www.usgo-archive.org/files/pdf/conciserules.pdf).

Canonical decoding rejects positive residuals after termination; browsing returns
the sequence ending there. Both directions enforce a 4096-ply work limit. This
format records play only: no scoring, result, komi, handicap setup, SGF metadata,
or post-scoring resumption. A small pure-Python rules engine keeps the same codec
available in the browser without adding dependencies. Tests cover connected
captures, suicide, immediate ko, a full triple-ko repetition, passes, terminal
aliases, all sizes, prefix equivalence, custom vocabularies, and frozen fixtures.

## Custom word lists and privacy

The same ordered list and normalization rules must be available to sender and
recipient. Order is part of the encoding; changing it changes the truenames.

Provide one shared workflow across CLI and browser:

1. Load a UTF-8 file with one word per line, or paste the equivalent list.
2. Validate the effective ordered vocabulary: empty lists, duplicate normalized
   tokens, embedded whitespace, and reserved prefix punctuation get clear errors.
3. Show its effective word count, capacity, and a deterministic identifier derived
   from the normalized ordered list and its normalization policy.
4. Encode and decode with that same list. Export the normalized file for a friend
   to import. Default-list use requires no configuration.
5. Show the vocabulary identifier beside shared truenames where practical, so friends
   can compare it with their selected list. Keep it distinct from type prefixes.

Define Unicode normalization and case handling once and test them across clients.
Do not silently sort, deduplicate, shuffle, trim internal text, or remove words.
Keep default vocabulary fixtures and include custom-list fixtures with different
sizes, ordering, and non-ASCII words. A smaller list requires more words and may
not have enough total capacity for a requested value.

**A private word list is not reliable encryption.** A known or guessed value can
reveal information about the mapping; deterministic truenames expose repeated values;
type prefixes reveal the type. A wrong list can produce a plausible, incorrect
decode. Its identifier helps choose a list but does not authenticate the message,
and may let someone test guesses about the list.

Recommend first-release wording of “private vocabulary” or “obscured encoding”,
with no claim that it safely stores passwords or protects sensitive information
from an attacker. Share private lists separately through an already trusted
channel. Do not put them into public links or browser logs.

If security means actual confidentiality, authenticated encryption and key sharing
must become an explicit requirement before implementation. Do not design custom
cryptography from word permutations. Encryption would add key-management UX and
payload overhead, and authentication failures necessarily sit outside the promise
that every short truename decodes. That is a release-scope decision, not a feature to
quietly append to this plan.

## Easy encoding and decoding

### Library and CLI

Keep one core path for parsing values, ranking, prefix handling, word conversion,
and canonical output. Expose encode, canonical decode, and explicit browse
operations. Every ordinary decode path, including convenience conversion, is
canonical by default. Select a type when parsing is ambiguous; never depend on
registry iteration order.

Use Tyro with a Pydantic command model as required by the project instructions.
Keep related dependency changes in their own commit. Support quoted arguments,
interactive use, and one input per line from stdin with the same semantics.
Do not treat `#` as a universal comment delimiter because it can belong to a
phone string or URL. Diagnostics go to stderr; failures produce a nonzero exit
status; successful piped output remains usable as data.

An encode result should make the canonical value, selected type/prefix, payload,
and vocabulary identity available to callers. A decode result should expose the
typed value and its canonical truename. Browsing additionally reports whether it
redirected a noncanonical input. Keep machine output limited to what the browser
and pipeline need rather than adding several competing output formats.

### Browser experience

The browser has description and true name panes side by side, beneath a centered
`nmr` heading and the subtitle "true names of canonical things". The left pane
always contains the editable field; the right contains clickable results. On small
screens the panes stack. Swap exchanges captions and puts the first converted
result into the editor. Without a conversion, swapping starts with an empty
editor so description text cannot violate the true name vocabulary rules.

description mode recognizes unprefixed details by shape and otherwise encodes
literal String text, including vocabulary words. true name mode uses a controlled
typed/guessed editor. All completed words are
unique vocabulary entries; the final fragment must start an unused word. Guessed
continuations are grey and selected randomly. Lowercase letters and Space enter
text; impossible letters and other editing keys produce a 20 ms tick at the
presentation root. Space accepts the suggestion. Right accepts at least one
character, continuing through forced characters until a branch or completion.
Completion adds a space and suggests an unused next word. Left and Backspace
return to the previous character choice, skipping forced stretches and removing
an automatic space at a word boundary. For example, Left takes `axis ` back to `a`.
Up/Down cycle matching continuations or eligible next words. The cursor stays at
the typed/guessed boundary; text can be selected and copied without moving that
editing position. Tab and focused
buttons retain keyboard accessibility. Type prefixes supplied by swaps or links
stay fixed outside word editing; loaded words normalize to lowercase.
`decode(..., browse=True)` receives completed, accepted words only. Neither a
partial word nor its guess changes or hides the description. Recognition responses
remain valid across partial edits when their accepted words are unchanged.
description output offers a prefix-relative truename and a `name:`-marked full
root truename. true name output offers the browsed object's description. Typed
descriptions such as `upc: 036000291452` and `string: "123"` preserve types on
swapping; String values use JSON quoting to preserve exact whitespace and quotes.

In description mode, typing, deletion, paste, native click placement, drag
selection, and double-click word selection remain supported. Recognition never
resets cursor or selection.
Right-hand results play their tunes at F3 and 180 BPM. Clicking the playing result
stops it; clicking another switches playback. In description mode, Enter plays
the first result unless the second has focus. Phone input rejects typed letters with a quiet tick.
The opening sound is `tune:the`, deferred to the first interaction if autoplay is
blocked. In description mode, Escape clears the editor and stops sound.

Conversion and tune arithmetic run locally through the shared Python core in a
Pyodide worker. The URL always contains one parameter: `desc` for description
mode or `name` for true name mode. Each edit and swap updates it through
`history.replaceState`, preserving the fragment without adding history entries
or issuing requests. On page load, this parameter restores the text and direction;
without either parameter, the editor starts with an empty description. The resulting URL can be bookmarked or sent
to a friend; opening or reloading it sends the query to the hosting server. The
app does not add analytics or persist the input in local storage.
The minimal browser uses the default vocabulary; explicit canonical decoding,
browsing, custom-list exchange, and other advanced operations remain available
through the CLI and library.

Publish several verified examples: a birthday, telephone number, coordinate,
reference containing leading zeroes, an IP address, a custom-list exchange, and a
short legal chess game. Show equivalent unprefixed, group-prefixed, and
leaf-prefixed truenames generated by the implementation.

## Delivery order and verification

### 1. Agree and record the release contract

The implementation choices are recorded in the final section: child placement,
chess identity, security expectations, browser delivery, `Float` representation,
type scope, and browsing limits. The four root categories, fixed radix four,
last-slot restriction, canonical decoding default, and permanent compatibility
are settled requirements. Record the prefix grammar, canonicalization
rules, stable allocations, and per-type bounds before changing encoders. Replace
pre-release fixtures deliberately, then freeze fixtures for the established format.

Exit criterion: every advertised type and scope has an unambiguous meaning and
an acceptance rule. There is no implicit architectural approval beyond this plan.

### 2. Repair and stabilize the core

Fix exact packing, registration, parse error handling, known data-loss bugs, and
installed-package word loading. Replace disabled or empty tests with meaningful
coverage of the corresponding behavior. Preserve unrelated worktree changes.

Exit criterion: existing supported codecs round-trip accurately; import order
does not change capabilities; installed-package checks succeed; known loss cases
are fixed or explicitly rejected pending their replacement codec.

### 3. Implement prefixes and completeness contracts

Add scope-relative rank/unrank using the chosen permanent allocation. Test each
type at leaf, group, and global scope, including verified equivalence triples,
word-count boundaries, and reserved slots. Verify canonical rejection and explicit
browsing separately, including agreement on canonical inputs. Simulate adding
children at multiple depths, including creating a category in an empty last slot
and extending through existing last-slot categories. Every previously canonical
truename must retain its meaning at every prefix scope. Verify radix four and
reject leaf allocations in slot 3 at every level, including the root. Verify that
the unnamed root cannot be nested and new category edges appear in the
corresponding prefix paths. Former browsing inputs may change discovery
results without invalidating those saved truenames.

Exit criterion: all advertised scope ranges satisfy their published guarantees,
and invalid syntax never masquerades as a browsing input.

### 4. Finish useful codecs and chess

Implement the agreed type matrix and the chosen chess enumeration. Use precise
definitions for dates, temporal resolution, phone structure, coordinates, `Float`
identity, Unicode, and semantic-version metadata. Test leap days, timezone offsets,
negative values, leading zeroes, poles, antimeridian, address limits, and metadata.

For `Frac`, test exact pair round trips for unreduced fractions, both denominator
signs, distinct zero numerators, and zero denominators. Test that `.float()` returns
the required infinities and NaN, `.fraction()` delegates reduction and rejects
zero denominators, and neither conversion changes the pair. Verify equality of
stored pairs rather than numerical equivalence. Cover the agreed finite overflow
policy without introducing numerical operators on `Frac`.

For chess, replay decoded moves to verify legality, test canonical round trips,
canonical rejection of terminal overrun, browsing of that overrun, castling,
en passant, promotion, and the agreed draw rules.
Do not confuse a parser accepting a FEN with proving its reachability.

Exit criterion: useful example values preserve their declared meaning, and every
promised complete browsing range has both a construction argument and tests of
its bounds.

### 5. Complete the recipient experience

Finish CLI behavior, custom-list exchange, and the local browser interface using
the same core. Measure representative truename lengths and browser load time. Have
someone unfamiliar with the project decode both a default-list truename and a
private-list truename using only the instructions they would receive from a friend.

Exit criterion: the recipient can identify the type, select the right vocabulary,
canonically decode, distinguish browsing from decoding, and copy the canonical
result without developer assistance. Private values and lists do not leave the
browser during conversion.

### 6. Release checks and documentation

* Test encode/canonical-decode/browse behavior, not private implementation details.
  Exhaustively enumerate small vocabularies and small codec domains; use fixed
  boundary and representative samples for large domains.
* Include arbitrary-precision cases above floating-point exactness, pair-number
  boundaries, vocabulary capacity limits, and every prefix scope.
* Keep shared compatibility fixtures for the library, CLI, and browser. Freeze
  word order, allocations, canonical semantics, prefix spelling, and move ordering.
  Prove extension compatibility with simulated new children, not only unchanged
  fixtures against the current registry. Never rely on a later incompatible format.
* Run the project's required pytest, Ruff, type-checking, and pyupgrade checks
  when implementation changes warrant them. Use `nmr` and `test` as the paths;
  the supplied `recs` check command is not the project truename here.
* Verify CLI failures and exit codes, wheel and source-distribution installs,
  bundled vocabulary access outside the checkout, and actual browser operation.
* Review user documentation for unsupported claims, especially security,
  completeness, compression, legal chess positions, and six-word capacity.
* Commit coherent changes separately, put tooling/dependency changes in their
  required separate commit, and push each commit. Publish only after the release
  scope and any distribution/hosting decisions are approved.

The later implementation authorization covers the runtime and packaging checks
described above. Live browser UI access was rejected by the approval gate, so
WebAssembly checks run without a browser and the UI checks are provided in CI.

## Resolved implementation decisions and delivery status

The later instruction requested an uninterrupted implementation with defaults
chosen autonomously. These replace the original question list; none requires a
human answer to use the delivered library, CLI, or static browser build.

| Original decision area | Implemented choice |
| --- | --- |
| Tree and placement | Four-way tree and explicit allocations above; no legacy decoder. Golden fixtures freeze the new format. |
| Security | Private vocabularies provide obscurity. Actual encryption, key management, and password storage claims are excluded. |
| Main use cases | The implemented type matrix; generic string encoding is excluded. |
| Browser delivery | Static local conversion through pinned Pyodide 0.29.3 in a worker, with the same bundled Python core. |
| Chess identity | Standard-start legal move sequences; unfinished and empty games count. FEN encoding is replaced. |
| Browsing | Explicitly selected; deterministic redirects through supported children, finite-domain modulo, codec-specific repairs. Canonical decoding remains the default. |
| Repetition | Repeated words are invalid in both modes. |
| Practical lengths | Generated examples show birthday: 2 words, international phone: 4, coordinate: 6, three-ply chess: 2. No universal shortness claim. |
| Prefixes | Full leaf paths by default. CLI/API can select an ancestor scope or no prefix. Paths are independent of vocabulary. |
| Temporal scope | Gregorian years 1–9999, exact microseconds, explicit offsets for instants, UTC canonical output. No partial dates, named timezones, leap seconds, or calendar-month durations. |
| Float and fraction conversion | Exact binary64 bits, including all NaNs and signed zero. Frac finite overflow raises; zero denominators convert to signed infinity or NaN. |
| Phones | International numbers up to 15 digits plus digit extensions; no regional inference, short codes, or vanity-number conversion. |
| Coordinates | Decimal degrees to six places, rejecting extra precision. Pole longitudes collapse to zero; +180 and -180 longitude are equivalent. |
| Additional identifiers | ISBN and UPC have checked compact codecs. Collections are not supported. |
| Vocabulary policy | NFC plus case folding by default; optional case sensitivity and active word count. Word order, normalization, and count participate in identity. Existing default order retained. |
| Vocabulary exchange | File import, paste, normalized export, and full SHA-256 identity. No automatic persistence or shuffling. |
| Typo handling | Strict canonical rejection and explicit result verification. No checksum overhead or silent correction. |
| Chess metadata and rules | Main line only, lexical UCI ordering, automatic endings enforced, maximum 4096 plies. |
| CLI continuity | Replaced the broken old interface with Tyro/Pydantic configuration. Encode, decode, browse, streams, JSON, vocabulary tools, and static build are supported. |
| Release delivery | Metadata prepared for 1.0.0; source and wheel builds and local static output. No external package publication or hosted deployment. |

### Completed slices

1. Added Tyro/Pydantic in a dedicated dependency commit and established the baseline.
2. Replaced the truename core, category allocation, numeric models, word validation,
   and CLI; removed the broken old codec implementations.
3. Added everyday codecs and legal chess enumeration.
4. Added the static browser build, worker bridge, vocabulary UI, and WebAssembly
   checks. Improved very-large-integer handling.
5. Added permanent cross-runtime fixtures, current CI, installed-artifact checks,
   documentation, and replacements for obsolete maintenance paths.
6. Added the requested Go extension in an unused leaf slot, preserving existing
   canonical truenames and sharing the implementation across Python and WebAssembly.
7. Removed the public Text type and its browser choice. Its former slot was
   unassigned; other types retain their truenames. Shared digit ranking remains for
   compact codecs.
8. Removed Record and its field-name encoding.
9. Removed List and the former `meta` category. All categories, including the root,
   now use four-way routing and reserve their last slot for categories.
10. Replaced repeated pairing with direct sum-layer tuple enumeration. For total
    `S` and arity `n`, the rank is `comb(S+n-1, n) + rank(tail)` with the one-part
    rank equal to its value. Unranking uses exact binomial comparisons and integer
    binary search, ending with the existing exact two-part inverse. Removed the
    forward/backward nested-pairing option. SemVer packs all five integer
    components directly. Two-part ranks and fraction truenames remain unchanged;
    SemVer fixtures deliberately adopt the new mapping without a legacy decoder.
    Balance is by component sum, not by bit length, so individual truenames can grow.

### Verification and limits

The final local suite has 167 tests with 94% branch-aware coverage. It passes on
CPython 3.10, 3.13, and 3.15. Clean wheel and source-distribution installs were
checked outside the checkout, including all format fixtures, vocabulary loading,
CLI decoding, and static browser builds. The source archive excludes unrelated
local editor and reflog files; browser bundles include project/dependency licenses.
The first remote install exposed host-specific cooldown settings in the lockfile.
Those settings were removed without changing package versions, and reproduction
commands now use frozen installs. A clean environment was checked independently.

The unit suite covers small-vocabulary permutations exhaustively, exact pairing
boundaries, prefix equivalence, canonical rejection, browsing, invalid data,
nonfinite values, collection identity, legal games, and CLI stream behavior.
`test/format.json` supplies published fixtures to both Python and WebAssembly
checks. Ruff, formatting, type checks, pyupgrade, and the coverage gate accompany
implementation tests. Automatic CI runs Python 3.10, 3.13, and 3.15 and an
independent non-UI WebAssembly job. Browser UI checks are a separate manual job;
they were not dispatched as a workaround for the local approval rejection.

The Node WebAssembly bridge was exercised locally with the actual static bundle.
Live browser interaction and visual QA could not run because browser approval
rejected local-preview access. The browser smoke test remains executable where
access is available and is wired into CI. Browser startup measured through the
non-UI runtime was approximately 1.8 seconds with cached runtime packages; this is
not a cold mobile-browser benchmark. No claim of human usability testing is made.

External distribution remains a deployment task: the repository contains a
buildable installation-free decoder, but no public URL or PyPI release was created.

### String fallback

`data:id:string` occupies slot 2 under `data:id`. It preserves case, allowed whitespace,
and Unicode composition exactly, including the empty string. It excludes
U+0000–001F, U+007F–009F (including DELETE), and surrogate code points U+D800–DFFF.
The character order is `a`–`z` (0–25), `A`–`Z` (26–51), the remaining allowed
U+0020–00FF code points in ascending order (52–190), then U+0100 upward, skipping
surrogates. The alphabet has 1,111,999 characters.

For a nonempty string of length `n`, let `p` be the shared `Packer(count=n)`
diagonal rank of its character indices. Its string index is
`((2*p + 1) << n) - 1`. The empty string has index zero. Decoding reads `n` from
the trailing zero bits of `index + 1`, then unpacks the remaining tuple rank.
This is the trailing-binary length tag, and distinguishes `a`, `aa`, and
`aaa`, whose character tuples all rank zero. Strict decoding rejects invalid
character indices and noncanonical empty-string aliases; browsing wraps invalid
character indices modulo the alphabet size and maps empty-string aliases to empty.
Vocabulary capacity still limits truename size. `dfasdfasdf` now has the truename
`string:she dump stan learn river`.

The GUI leaves an empty field empty, but explicit library/CLI String encoding
supports the empty string. String is the fallback for otherwise unrecognized
input; only explicit incomplete type syntax waits for completion.
