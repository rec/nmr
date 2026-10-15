# nmr: plan for a useful first release

## Purpose and scope

Give people a practical way to turn their important details into short, reproducible
word names, share those names, and let friends recover the original details easily.
Keep the more playful ambition: a short name can also discover an interesting,
valid object, including a legal chess game.

This is a plan, not an authorization to implement every proposed design. The
recommendations below define a bounded first release; unresolved decisions are
collected at the end. Implementation should follow those decisions rather than
silently choose incompatible meanings.

Additional work beyond the prompt: None.

The release should provide:

* A dependable Python library and command-line tool.
* A small, mobile-friendly browser encoder/decoder that friends can use without
  installing Python, registering, or uploading their private details.
* Useful codecs for common personal details, with an exact text escape hatch for
  details that do not justify their own codec.
* Optional hierarchical prefixes that reveal the type and reduce the integer
  encoded by the word payload, while retaining existing numeration.
* Straightforward custom-word-list creation, loading, and sharing.
* Explicit guarantees about canonical names, losslessness, completeness, capacity,
  and the limits of privacy.

Do not include accounts, cloud storage, social features, native mobile apps,
contact synchronization, or a general plugin marketplace in this release. Music,
chemistry, and additional board games remain outside the release unless chosen
to replace another scoped feature.

## What the repository already provides

This assessment is from reading the code and tests, not running them.

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
| Type selection | `get_class` refers to an undefined variable and builds its lookup from metaclass names; parsing catches every exception. | Deterministic type lookup; expected parse failures separated from programming errors; explicit ambiguity handling. |
| Registration | Import order controls availability, and reserved categories can reach missing codecs. | One deliberate supported-type registry; independent of test import order; unsupported slots handled according to the chosen completeness contract. |
| Coordinates | Longitude formatting modifies latitude; latitude endpoints are conflated; precision documentation disagrees with the scale. | Correct hemispheres and boundaries, defined coordinate equivalence, explicit resolution, and no silent precision loss. |
| Semantic versions | Prerelease and build metadata are parsed but discarded during encoding. | Preserve the complete supported version or reject unsupported forms before encoding. |
| Time | Duplicate class definitions, undefined names, mismatched constants, incomplete decoders, approximate calculations. | Replace the unfinished implementation with the agreed, exact date/time codecs. |
| Phone numbers | Duplicate definitions and copied semantic-version code. | A working, clearly bounded phone codec. |
| Chess | Encodes FEN fields; arbitrary decoded fields need not form a legal position, and positions do not preserve a game's moves. | Separate the promised object and legality guarantee before choosing its enumeration. |
| CLI | Disabled tests, unused options, disconnected random generation, ignored stored error status, and argument quoting that can alter input. | A coherent, tested command interface, faithful input handling, and meaningful exit codes. |
| Words | Empty input, repetition, token syntax, and normalization are not a consistent public contract. | One documented grammar enforced across library, CLI, and browser. |
| Packaging/docs | Word file is located outside the package; README/API examples are stale; time tests contain no cases. | Verify installed wheels and source distributions, bundle the vocabulary reliably, and publish executable examples. |

The working tree currently has an unrelated `CARDS` to `CARD` edit in
`nmr/category.py`; preserve it. `TAGS` and `reflog.txt` are also outside this plan.

## Define the format before adding codecs

### Canonical values and names

For a fixed format, ordered vocabulary, and prefix scope:

1. Every supported canonical value has exactly one canonical name within capacity.
2. Decoding that name recovers the same typed canonical value.
3. Different canonical values of the same type never share a canonical name.
4. Different prefixes may give different names for the same typed value.
5. A decodable noncanonical name may normalize to another name for the same value.

Distinguish value preservation from spelling preservation. For example, equivalent
IPv6 spellings may have one canonical output; a phone identifier must retain
meaningful leading zeroes; exact text must retain its original contents. Display
normalization before encoding whenever the input spelling will change. Do not
round, truncate, infer a country, or discard timezone information silently.

Freeze existing category numbers, radices, and default word order before changing
registration. Record fixtures for working historical encodings. Prefixes must
not renumber them. Repairs to lossy codecs may require a format decision: retain
unaffected mappings, identify incompatible cases explicitly, and decide the
release policy before shipping. Do not build a legacy decoder without a confirmed
need. The default dictionary must not be silently reordered or cleaned up.

### Hierarchical prefixes

Use a colon-separated path followed by a word payload:

* No prefix: words encode the existing global integer.
* `game:`: words encode the integer inside the existing game group.
* `game:chess:`: words encode the integer inside the chess subtype.

Let `g` and `s` be the existing zero-based group and subtype numbers, `R_G` the
group radix, `R_g` the group's subtype radix, and `n` the type-relative integer.
The existing global integer is:

`I = g + R_G * (s + R_g * n)`

The corresponding payload integers are `I`, `s + R_g * n`, and `n`. Decoding a
prefix restores the omitted fixed components. For the current chess category,
these are `21 + 64*n`, `2 + 8*n`, and `n`. This makes the three forms equivalent
without changing the word-ranking algorithm.

Keep prefixes outside the vocabulary. A custom list changes the payload words,
not the spelling or meaning of `game:chess:`. A prefix restricts decoding to its
scope; it must never be treated as a hint that the decoder can ignore. Remove a
prefix only by decoding and re-encoding, never by deleting its text.

Use exact, documented prefix names, normalized consistently across clients. Do
not initially add abbreviations or synonyms. Reject unknown paths, missing
payloads, and extra path components with useful errors. Explicit encode/decode
operations must distinguish a prefixed name from raw values containing colons,
such as IPv6, timestamps, or URLs.

Recommend the most specific prefix as the default output, with an explicit
selection for a broader or unprefixed scope. A narrower scope cannot increase
the canonical payload word count for the same type-relative integer, but the
prefix may make the whole printed name longer. Show actual counts rather than
promise a fixed saving.

The example `they see what they may` repeats `they`, contrary to the existing
nonrepetition rule. Treat the supplied examples as illustrations of scope, not
valid equivalence fixtures. Recommended policy: retain nonrepetition and replace
them with generated, verified examples. Whether repeated words should become
accepted noncanonical input is a question for the format decision.

### Completeness and finite capacity

Completeness means that every syntactically valid payload inside a published
range decodes to an object satisfying the type's stated validity rules. It does
not mean that every arbitrary sentence is a name, or that every name is canonical.

For a vocabulary of size `W`, the number of nonempty, nonrepeating payloads of
at most `k` words is:

`C(W, k) = sum(W! / (W-j)!, j=1..min(k, W))`

Those names represent indices `0 <= n < C(W, k)`. Even an unbounded integer type
has finite representable capacity with a finite nonrepeating vocabulary. Report
overflow clearly and offer a larger vocabulary; never silently discard data.

Publish completeness per scope and codec, with a bound expressed as an index
range and the corresponding word lengths for the chosen vocabulary. Distinguish:

* Exact canonical round-trip support for values inside capacity.
* Total decoding of all payload indices inside the promised bound.
* Syntactic validity, semantic validity, and externally verifiable facts.

For finite dense types, canonical indices cover the finite domain. Higher indices
can be noncanonical aliases through a documented modulo rule, if approved. For
structured types, rank valid objects directly where practical. Do not promise
completeness through searching until something happens to be valid.

For a group or the global scope, completeness additionally requires a stable
answer for every reserved or unimplemented category slot. The current wrap by
enum length is not sufficient and changes meaning as categories are added.
Recommended first-release guarantee: complete supported leaf scopes, and broader
scopes only where their entire advertised range is covered. If global completeness
is required, freeze an explicit alias allocation for unused slots and decide how
future formats can reclaim them without changing saved names. Never silently
reinterpret historical canonical names.

Always show the canonical name after decoding an alias. Accepting aliases cannot
also guarantee detection of mistyped names: many mistakes will be other valid
objects. This limitation must be visible in the sharing flow.

## First-release type coverage

“All common types” needs a finite release definition. The following is the proposed
coverage. The exact-text codec supplies faithful coverage for personal details
outside these specialized codecs, without inventing jurisdiction-specific rules.
Allocate new leaf identifiers only after checking spare slots and compatibility.

| Type | First-release scope and canonicalization | Completeness target |
| --- | --- | --- |
| Integers | Signed arbitrary-size integers, limited by vocabulary capacity. | Every payload index. |
| Fractions | Exact reduced rational values with positive denominator. Preserve existing mappings where correct. | Every payload index; unreduced representations may be aliases. |
| Decimal numbers | Exact finite decimal values; specify treatment of trailing zeroes and negative zero. Avoid binary floating-point conversion. | Every payload index through a defined sign/coefficient/scale enumeration. |
| Dates | Gregorian calendar dates, including birthdays; recommend years 1 through 9999 initially. | Dense day enumeration; approved aliases beyond the finite range. |
| Times and timestamps | Separate time of day, local date-time, and offset-aware timestamp meanings. Recommend microsecond resolution and explicit offsets initially. | Enumerate valid components, with precisely bounded domains. |
| Durations | Signed elapsed time with exact supported resolution. Calendar months/years are not fixed durations. | Every payload index in the defined representation. |
| Phone numbers | International numbers with explicit country calling code and optional extension; preserve significant digits. No implicit regional parsing. | Structural validity only; no claim that a number is assigned or reachable. |
| Coordinates | Latitude/longitude at a declared fixed resolution, with poles and antimeridian equivalence specified. | Every canonical grid point; aliases only under documented rules. |
| IP addresses | IPv4 and IPv6; canonical standard spelling. Decide scoped IPv6 separately. | Full address domains, including non-routable addresses. |
| UUIDs | Preserve all 128 bits; do not invent UUID-version constraints. | Full 128-bit domain. |
| Semantic versions | Major, minor, patch, prerelease, and build metadata. | Canonical round trips; a total valid enumeration only if achievable within the release. |
| Exact text | Names, postal addresses, email addresses, URLs, account/reference identifiers, and short notes. Preserve whitespace, case, punctuation, and leading zeroes. | A reversible enumeration of supported Unicode scalar strings, including empty text; capacity remains finite. |
| Chess | A legal move sequence from the standard initial position, subject to the decision below. | Every payload index within the advertised practical bound. |

The browser should offer recognizable input choices such as “email”, “address”,
and “reference number” backed by exact text, explaining that these share the text
type and do not validate ownership, delivery, or account existence. Avoid making
regex acceptance look like semantic validation. Structured email, URL, ISBN, or
bank codecs should be added only if their measured benefit justifies inclusion
before release.

Text coverage is important, but arbitrary long text will not become a few words.
Measure realistic output lengths for every proposed use case. If common details
produce impractically long names, revise the release scope or representation
before describing the product as easy to share. Do not add compression or contact
bundles without a demonstrated need and an explicit decision.

## Chess: legal games and positions

The existing code names FEN positions, not games. A valid FEN structure does not
prove that a position is reachable from the standard starting position. A game
also includes its move sequence; several games can lead to the same position.

Recommended first-release object: a finite sequence of legal moves from the
standard initial position, including an unfinished game. Accept a simple move
sequence or PGN main line; explain that comments, variations, and headers are not
part of the named object unless separately included in the agreed scope.

A concrete complete enumeration is the rooted tree of legal games:

1. Index zero denotes the current move sequence ending here, including the empty
   sequence at the initial position.
2. At a nonterminal position, order legal moves by a frozen, documented move
   notation, not by library iteration order.
3. For positive index `n`, divide `n-1` by the number of legal moves. The remainder
   selects a move and the quotient continues from the resulting position.
4. At a terminal position, any remaining index denotes an alias of the sequence
   that ends there. Encoding the move sequence produces its canonical index.

This constructs reachable games directly and supports inverse ranking without
enumerating all positions. Freeze automatic termination rules, including draws,
and distinguish claimable draws from automatic endings. Measure work for extreme
indices before publishing a word-length guarantee; enforce limits before decoding,
not after silently truncating the game.

This proposed representation is incompatible with the existing FEN codec if it
uses the same leaf identifier. Decide whether `game:chess:` continues to mean a
position or becomes a game before implementation. If historical position names
must survive, retain that identity and allocate a distinct game leaf. If positions
remain the main object, legal-game aliases need a separate, explicit design;
the existing FEN field packing cannot provide the requested legality guarantee.

## Custom word lists and privacy

The same ordered list and normalization rules must be available to sender and
recipient. Order is part of the encoding; changing it changes the names.

Provide one shared workflow across CLI and browser:

1. Load a UTF-8 file with one word per line, or paste the equivalent list.
2. Validate the effective ordered vocabulary: empty lists, duplicate normalized
   tokens, embedded whitespace, and reserved prefix punctuation get clear errors.
3. Show its effective word count, capacity, and a deterministic identifier derived
   from the normalized ordered list and its normalization policy.
4. Encode and decode with that same list. Export the normalized file for a friend
   to import. Default-list use requires no configuration.
5. Show the vocabulary identifier beside shared names where practical, so friends
   can compare it with their selected list. Keep it distinct from type prefixes.

Define Unicode normalization and case handling once and test them across clients.
Do not silently sort, deduplicate, shuffle, trim internal text, or remove words.
Keep default vocabulary fixtures and include custom-list fixtures with different
sizes, ordering, and non-ASCII words. A smaller list requires more words and may
not have enough total capacity for a requested value.

**A private word list is not reliable encryption.** A known or guessed value can
reveal information about the mapping; deterministic names expose repeated values;
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
that every short name decodes. That is a release-scope decision, not a feature to
quietly append to this plan.

## Easy encoding and decoding

### Library and CLI

Keep one core path for parsing values, ranking, prefix handling, word conversion,
and canonical output. Expose explicit encode and decode operations plus the
existing convenience conversion only where input is unambiguous. Select a type
when parsing is ambiguous; never depend on registry iteration order.

Use Tyro with a Pydantic command model as required by the project instructions.
Keep related dependency changes in their own commit. Support quoted arguments,
interactive use, and one input per line from stdin with the same semantics.
Do not treat `#` as a universal comment delimiter because it can belong to a
phone string or URL. Diagnostics go to stderr; failures produce a nonzero exit
status; successful piped output remains usable as data.

An encode result should make the canonical value, selected type/prefix, payload,
and vocabulary identity available to callers. A decode result should expose the
typed value and its canonical name, including whether the supplied name was an
alias. Keep machine output limited to what the browser and pipeline need rather
than adding several competing output formats.

### Browser experience

Treat an installation-free decoder as part of first-release usefulness. Start
with a small accessible page: paste a name, optionally load a list, decode, and
copy the result. An encode view selects the type, accepts the value, previews its
canonical interpretation, and shows the name and word count. Use full leaf
prefixes by default so the recipient can recognize the kind of detail immediately.

Run conversion locally in the browser. Choose the smallest practical way to reuse
the Python core, and measure mobile load time before committing to a browser
runtime or dependency. Do not independently reimplement the arithmetic in
JavaScript. If Python-in-browser is too heavy, bring that tradeoff back for a
decision rather than quietly introduce a server handling private values.

Default to copying a name as text. Do not automatically put sensitive input into
URLs, history, analytics, or persistent storage. Keep imported lists in memory
until the user explicitly chooses otherwise. Show clear errors for unknown
prefixes, unrecognized words, insufficient capacity, and mismatched vocabulary
identifiers when one is supplied. Do not guess corrections and decode them
silently. Show the result for human verification because valid-word substitutions
cannot generally be detected by a complete decoder.

Publish several verified examples: a birthday, telephone number, coordinate,
reference containing leading zeroes, an IP address, a custom-list exchange, and a
short legal chess game. Show equivalent unprefixed, group-prefixed, and
leaf-prefixed names generated by the implementation.

## Delivery order and verification

### 1. Agree and record the release contract

Resolve the blocking questions below: format compatibility, chess identity,
security expectations, browser delivery, type scope, and completeness. Write the
prefix grammar, canonicalization rules, stable identifiers, and per-type bounds
before changing encoders. Capture working historical fixtures first.

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

Add scope-relative rank/unrank using existing identifiers and radices. Test each
type at leaf, group, and global scope, including verified equivalence triples,
word-count boundaries, reserved slots, and canonicalization of aliases. No-prefix
fixtures remain stable except for explicitly approved incompatible repairs.

Exit criterion: all advertised scope ranges satisfy their published guarantees,
and invalid syntax never masquerades as an alias.

### 4. Finish useful codecs and chess

Implement the agreed type matrix and the chosen chess enumeration. Use precise
definitions for dates, temporal resolution, phone structure, coordinates, decimal
scale, Unicode, and semantic-version metadata. Test leap days, timezone offsets,
negative values, leading zeroes, poles, antimeridian, address limits, and metadata.

For chess, replay decoded moves to verify legality, test canonical round trips,
terminal aliases, castling, en passant, promotion, and the agreed draw rules.
Do not confuse a parser accepting a FEN with proving its reachability.

Exit criterion: useful example values preserve their declared meaning, and every
promised complete codec has both a construction argument and tests of its bounds.

### 5. Complete the recipient experience

Finish CLI behavior, custom-list exchange, and the local browser interface using
the same core. Measure representative name lengths and browser load time. Have
someone unfamiliar with the project decode both a default-list name and a
private-list name using only the instructions they would receive from a friend.

Exit criterion: the recipient can identify the type, select the right vocabulary,
decode, recognize normalization or aliases, and copy the result without developer
assistance. Private values and lists do not leave the browser during conversion.

### 6. Release checks and documentation

* Test encode/decode/canonicalize behavior, not private implementation details.
  Exhaustively enumerate small vocabularies and small codec domains; use fixed
  boundary and representative samples for large domains.
* Include arbitrary-precision cases above floating-point exactness, pair-number
  boundaries, vocabulary capacity limits, and every prefix scope.
* Keep shared compatibility fixtures for the library, CLI, and browser. Freeze
  word order, category numbers, prefix spelling, and move ordering.
* Run the project's required pytest, Ruff, type-checking, and pyupgrade checks
  when implementation changes warrant them. Use `nmr` and `test` as the paths;
  the supplied `recs` check command is not the project name here.
* Verify CLI failures and exit codes, wheel and source-distribution installs,
  bundled vocabulary access outside the checkout, and actual browser operation.
* Review user documentation for unsupported claims, especially security,
  completeness, compression, legal chess positions, and six-word capacity.
* Commit coherent changes separately, put tooling/dependency changes in their
  required separate commit, and push each commit. Publish only after the release
  scope and any distribution/hosting decisions are approved.

No Python tests are needed for this planning-only change. Subsequent implementation
verification should follow project instructions; running services or full runtime
flows requires the corresponding authorization.

## Questions for the undertaking

These are the foreseeable decisions for this first release. The recommendations
above let implementation stay small, but the following answers can change the
format, security promise, or public behavior. Resolve questions 1 through 8 before
substantial implementation; settle the remainder before their associated phase.

1. **Existing users and names:** Are any current names in real use? Must every
   historical working encoding remain readable, or may this release fix mappings
   incompatibly? If incompatibilities are necessary, how should a recipient
   identify the format version?
2. **Meaning of security:** Is obscurity through a privately shared vocabulary
   sufficient, or must this release protect details against someone actively
   trying to recover them? If confidentiality is required, what threats and
   password/key-sharing experience must it support?
3. **Main use cases:** Which details do you most want people to share first?
   Are birthdays, phones, coordinates, exact-text contact/reference details, and
   computer identifiers the right coverage, and what must be added or removed?
4. **Ease of access:** Is a mobile-friendly, locally executing browser tool a
   first-release requirement? Is reusing Python through a browser runtime
   acceptable, subject to measured download and startup costs?
5. **Meaning of chess:** Should `game:chess:` identify a move sequence, a position,
   or a completed game? Must unfinished games and the initial position count?
   Do existing FEN names need preservation under their current identifier?
6. **Completeness scope:** Is complete decoding of supported leaf prefixes enough
   initially, or must every short group-prefixed and unprefixed name also decode?
   May unused type slots become frozen aliases, with consequences for future
   category allocation?
7. **Aliases and repetition:** May finite types use modulo aliases beyond their
   canonical range? Should repeated words remain invalid, or did the repeated
   `they` in the example intentionally request a new accepted input form?
8. **Acceptance thresholds:** What maximum word counts feel useful for the main
   details, and what minimum “short enough” completeness range should chess and
   the other types guarantee? What browser load and decoding times are acceptable
   on an ordinary phone?
9. **Prefix UX:** Should full leaf prefixes be the default, as proposed? Are
   existing group names such as `commercial` and `location` suitable for users,
   and should custom lists always retain the same English prefix names?
10. **Dates and time:** Are Gregorian years 1 through 9999 and microseconds enough?
    Do we need partial dates such as month/day birthdays, named timezones, leap
    seconds, or calendar durations in this release? How should ambiguous numeric
    dates and offset-free date-times be presented?
11. **Numeric identity:** Are decimal trailing zeroes and negative zero meaningful
    details to preserve, or should equal numeric values share one name? Is exact
    decimal support sufficient without a separate binary floating-point codec?
12. **Phone scope:** Are explicit international numbers plus extensions sufficient,
    or are local numbers, short codes, `*`/`#` service strings, and vanity numbers
    required? If local numbers are supported, how will users supply the region?
13. **Coordinate identity:** What precision is useful, and should pole longitudes
    and the two antimeridian spellings be equivalent? Should excess input precision
    be rejected or rounded only after explicit user confirmation?
14. **Text and contact details:** Is exact text an acceptable first-release backing
    for email, URLs, postal addresses, and reference numbers? Must the decoded name
    retain those semantic labels? Are multiline text and non-Latin scripts needed?
15. **Additional compact identifiers:** Are ISBN, product codes, bank identifiers,
    scoped IPv6 addresses, or a bundle of several contact details mandatory for
    the first release rather than adequately served by exact text or separate names?
16. **Vocabulary rules:** Should custom lists be case-insensitive? Which Unicode
    normalization, punctuation, and comment rules should apply? Must the current
    default list remain unchanged, including words that may be awkward or offensive?
17. **Vocabulary exchange:** Is importing an ordered text file sufficient for
    friends, or is a built-in list authoring/shuffling tool essential? May exported
    share text include a vocabulary identifier, and should the browser remember
    lists only through an explicit opt-in?
18. **Mistakes in shared names:** Is showing the decoded value and canonical name
    sufficient, or is a checksum required despite extra length? If required, how
    should checked messages coexist with the completeness of ordinary names?
19. **Chess details:** Are standard chess and PGN main-line moves enough? Must PGN
    metadata, variations, custom starting positions, resignation, agreed draws,
    or claimed draws be preserved? Which automatic termination rules define the
    enumerated games?
20. **CLI continuity:** Which existing CLI options and public Python entry points
    are actually used and must remain? May nonfunctional options be replaced by
    the single agreed interface rather than retained as compatibility wrappers?
21. **Release identity and delivery:** Which Python versions and browsers must be
    supported, what version denotes this first usable release, where should the
    browser tool live, and which package publication and hosting actions are
    authorized when implementation is ready?
