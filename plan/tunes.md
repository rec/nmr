# Truenames for short tunes

## Purpose and contract

Finding truenames for short tunes is nmr's original motivating purpose. A tune contains both
melody and rhythm, and its truename should recover something a friend can hear.
This plan supersedes the treatment of music as optional and transposition as
undecided in the other planning documents.

The goal is a bijection between nonnegative integers and a precisely defined
space of canonical tunes. In particular, decoding an integer must construct a
tune directly, without repairing invalid notes, searching for a playable object,
or folding several indices onto one result.

For a fixed vocabulary and the full tune prefix, every representable payload
index should identify exactly one canonical tune. Every canonical tune whose
index fits that vocabulary gets exactly one canonical payload. Equivalent input
spellings normalize before ranking.

There is one unavoidable capacity qualification: a finite vocabulary with no
repeated words has finitely many truenames. It cannot encode an infinite tune space.
The integer bijection is unbounded; a selected vocabulary truenames its initial
finite segment. Out-of-capacity tunes get an explicit error, not a shortened or
approximate substitute. Other prefix scopes and vocabularies have their own
truenames for the same tune, as elsewhere in nmr.

The slices below are implemented in `nmr/types/tune.py`, the shared browser
bridge, and browser playback. The current minimal browser accepts interval text
in its single controlled field; the earlier note-row editor has been replaced.
The enumeration and format fixtures define the first tune profile. Browser interaction verification remains blocked in the
current environment; see the verification notes below.

Additional work beyond the prompt: None.

## Musical identity

Use the following fixed first-profile rules. The user-established requirements
are combined melody and rhythm, successive pitch differences, presentation
centered around C or a configurable root note, and divisions by two and three.
Semitone resolution, beat semantics, and silence handling below are explicit
design defaults. Centered presentation replaces the earlier first-note-C rule;
the first relative pitch remains zero internally.

* A tune is a nonempty, finite, monophonic sequence of attacked notes. Chords and
  overlapping notes are outside this profile.
* Store each pitch after the first as a signed interval from the previous
  sounding note. Do not store note letters or a key signature in the identity.
* Use integer semitone differences in twelve-tone equal temperament. Preserve
  direction and octave distances; do not reduce intervals modulo twelve.
  Microtonal grids would require a separately allocated profile, not a local
  setting that changes the meaning of existing truenames.
* The first relative pitch is implicitly zero. Presentation centers the sequence
  around a configurable root, default C4, using the rule below. Changing the
  presentation root or transposing every input pitch equally does not change
  the truename. The first sounding note need not be C.
* There is no inferred scale or tonic. Centering on C does not make the tune
  C major. Chromatic intervals remain available.
* Each note has an exact positive duration in beats. Each later note also has
  an exact nonnegative gap after the preceding note ends.
* Playback tempo, timbre, velocity, written enharmonic spelling, meter, barlines,
  and beaming are presentation choices, not encoded identity.
* The beat remains a reference unit. Doubling every encoded beat duration gives
  a different rhythm; changing playback BPM alone does not. Do not silently
  normalize the first duration to one. Full proportional-rhythm equivalence
  would be a different identity decision.
* Leading and trailing silence are outside the encoded phrase. Remove them from
  keyboard or imported performance input before producing interval notation,
  and show that normalization before encoding. Interval text itself must start
  with `@`, never a rest or offset. Reject an empty or all-rest input.
* Merge adjacent rests into one intervening gap. Tied notes form one sustained
  note. Two attacks at the same pitch remain two notes, even with no gap.
* A rest does not reset the pitch reference: the next interval is measured from
  the previous sounding note.

These rules truename an abstract musical phrase, not a performance or score file.
There is no requirement that a generated tune be pleasant or recognizable.

## What divisions by two and three mean

Interpret this as rhythmic subdivision of a beat. Every duration or positive
gap must be a rational number whose reduced denominator has no prime factors
other than two and three, and at most one factor of three:

    d = u / (2^a * 3^b)
    u >= 1; a >= 0; b in {0, 1}

The fraction must be reduced: if `a > 0`, `u` is odd; if `b > 0`, `u` is not
divisible by three. There is no restriction that the numerator itself contain
only factors two and three.

Examples include `1`, `1/2`, `1/3`, `1/6`, `1/8`, `1/12`, `2/3`, `3/2`, and
`7/4`. This covers arbitrary binary subdivisions, triplets, and binary
subdivisions of triplets, but excludes nested triplets such as `1/9` and `1/18`.
Adding or tying allowed durations always produces another allowed duration.
A five-beat note is allowed; one fifth of a beat is not. A quarter note split
into three equal parts is allowed.

Reduce fractions before validation. Thus `2/6` and `3/9` mean `1/3`, while `1/5`
and `1/9` are rejected. Accept exact supported decimal fractions if useful, but
never round an approximate decimal to a triplet. Use `fractions.Fraction`
internally; duration equivalence differs deliberately from nmr's pair-preserving
Frac type.

Keep exact beat durations rather than dividing every duration by the first one:
scaling a five-beat first note to one could turn a later one-beat note into the
unsupported duration `1/5`. Ignoring playback BPM does not require changing the
encoded beat reference.

## Canonical input and output

Provide a compact interval-and-duration notation. For example:

    @1 2@1/2 2@1/2 r@1/3 -1@2/3 @1

This means an initial note lasting one beat, two successive upward semitone-pair
steps lasting half a beat each, a one-third-beat rest, a downward semitone step
lasting two thirds, and a repeated attack at that pitch lasting one beat.

The first token is `@duration`: a phrase must start with `@`, with no initial
offset, even an explicit zero. Later note tokens are `step@duration`, with no
`+` on positive steps. A later zero step may be written `0@duration` or
`@duration`; canonical output always omits the zero. Rest tokens use `r@duration`.
Durations print as reduced fractions, or integers when their denominator is one.
Canonical output has one space between tokens, with no edge rests or adjacent
rest tokens. Same-pitch attacks are never merged automatically.

The UI may accept absolute pitches through a keyboard or note editor, then
convert them to successive differences and discard the initial absolute pitch.
Show the normalized phrase and allow playback before encoding. The core numeric
notation does not need note truenames to represent the melody.

## Presentation centering

Center the cumulative sounding pitches, not the written intervals. Recover
relative pitches from the interval sequence as follows:

    p1 = 0
    pi = p(i-1) + step_i
    S = sum(pi)
    mean = S / m

Use the arithmetic mean over the `m` attacked notes, counting repeated notes
separately. Rests do not contribute, and note durations do not weight the mean.
Round to the nearest semitone, with exact half-semitone ties away from zero.
For example, `0.4` rounds to `0`, `0.6` to `1`, `-0.6` to `-1`, and `+/-0.5`
to `+/-1`. Compute the rounded center `k` using exact integer arithmetic:

    k = sign(S) * floor((2*abs(S) + m) / (2*m))

With configured root pitch `R`, present each note at:

    presented_pitch_i = R + pi - k

For the example phrase, the intervals are `0, 2, 2, -1, 0`, while the cumulative
pitches are `0, 2, 4, 3, 3`. Their mean is `12/5 = 2.4`, so `k = 2`. The
presented offsets from the configured root are `-2, 0, 2, 1, 1`. With C4 as the
root, these sound as Bb3, C4, D4, Db4, Db4, using one possible enharmonic spelling.
Averaging the intervals instead would yield `0.6`; that is not the centering rule.

Use the same placement for playback and absolute-pitch displays. The exact
arithmetic mean can remain within half a semitone of the configured root because
the placement shifts by whole semitones. Changing the root transposes the entire
presentation; it must not change the interval text, ranking, or canonical truename.
Centering is a presentation transform, not a step in the integer enumeration.

## A dense duration enumeration

Do not independently pack `(u, a, b)` and then reduce the fraction. That would
assign several integers to the same duration, defeating invertibility.

Instead enumerate only reduced durations, in finite complexity layers. Set
`h = floor(log2(u))`, computed using integer bit length, and define:

    weight = 4*h + a + 3*b

The numerator bit-length costs four per step, delaying long durations. Binary
subdivision costs one per step. The optional factor of three costs three,
so thirds arrive modestly later; further factors of three are excluded. These
weights define the enumeration, not playback settings; freeze them before truenames
are published. This favors short binary durations, including very short ones,
so assess the musical balance through playback during implementation.

Visit weights in ascending order. Within a weight, visit `h` in ascending order,
then `b` in ascending order over `{0, 1}`; `a = weight - 4*h - 3*b` is determined.
Visit `h <= floor(weight/4)` and omit groups with `a < 0`. For each group,
visit permitted numerators `u` in ascending order in:

    2^h <= u < 2^(h+1)

Omit numerators divisible by two when `a > 0`, and by three when `b > 0`.
Assign consecutive duration indices `D(d)`, starting at zero. The beginning is:

| Index | Duration in beats |
| --- | --- |
| 0 | 1 |
| 1 | 1/2 |
| 2 | 1/4 |
| 3 | 1/8 |
| 4 | 1/3 |
| 5 | 1/16 |
| 6 | 1/6 |
| 7 | 2 |
| 8 | 3 |
| 9 | 1/32 |
| 10 | 1/12 |
| 11 | 3/2 |

Compared with the unweighted `h + a + b` ordering, two beats move from index 3
to 7, four beats from 10 to 22, and thirds from 2 to 4. Ninths are excluded.

Every allowed positive duration appears exactly once: reduced numerator and
denominator exponents are unique, and they determine exactly one group. Every
group is finite, and every weight has entries (`1/2^weight` is always present).
Thus all nonnegative duration indices have inverses without aliases or holes.

Rank and unrank by counting groups, not by visiting every numerator. For a group
with inclusive numerator bounds `L` and `U`, let:

    multiples(k) = floor(U/k) - floor((L-1)/k)

Its size is `U-L+1`, subtracting `multiples(2)` if needed and `multiples(3)` if
needed, then adding back `multiples(6)` if both restrictions apply. The same
counting function on a prefix of `[L,U]` permits binary-search unranking of the
numerator. Cache or derive exact layer/group prefix counts for larger weights.

This ordering also avoids an important computational trap: directly packing
unbounded denominator exponents can make a short integer demand a denominator
with an astronomically large number of digits. Here, for `w >= 1`, weight `w`
has at least `2^ceil(w/4)-1` preceding entries from integer durations alone.
For duration index `r`, this gives `w <= 4*floor(log2(r+1))`; index zero has
weight zero. Also `a <= w`, `b <= 1`, and `h <= floor(w/4)`.
Consequently denominator exponents and numerator bit-length remain bounded by
the duration index's bit-length, not its numeric value. Construct fractions only
after checking work estimates.

## Encode melody and rhythm together

Enumerate complete tunes by total musical complexity. Each attack costs one;
steps from -2 through +2 semitones have no extra cost, and larger steps cost
`abs(step)-2`; durations retain weight
`4*h+a+3*b`; a positive gap costs one plus its duration weight. No gap costs zero.

    C = m + sum(duration_weight(di))
          + sum(max(0, abs(step_i)-2) + gap_weight(gi), i >= 2)

There is no separate length header or tuple rank. A greater number of simple
notes competes with fewer complicated notes in the same cost budget. Eight
repeated one-beat notes cost eight; one 128-beat note costs twenty-nine.

Visit costs in ascending order. Within a cost, visit the first duration in its
existing duration-index order. For each later note, visit pitch steps in order
`0,+1,-1,+2,-2,...`, then the gap (zero first, then positive duration-index
order), then its duration in duration-index order, then the next note. Only
choices with a completion at the remaining cost occupy a block. End the phrase
when no cost remains. The first note never has a pitch step or gap.

Every cost layer is finite, every tune has a finite positive cost, and each
canonical tune occurs in one block exactly once. Consecutive indices over those
blocks therefore give a bijection with nonnegative integers.

## Rational counting and inversion

Use rational generating functions for all counting tables, including duration
counts and cumulative layer counts. Let `D(z)` count durations by their weight.
For the default weights it is:

    D(z) = (1-z^5)(1+z^3+z^4) / ((1-z)(1-2z^4)(1+z^4))

More generally, with `x=z^BINARY_COST`, `t=z^NUMERATOR_COST`, and
`s=z^THIRD_COST`, it is `(1-xt)(1+t+s)/((1-x)(1-2t)(1+t))`.
The numerator filters count reduced fractions, including the numerator one.
For the default attack, step, and rest costs of one, define:

    P(z) = 5+2z/(1-z)        # five free steps, then two at each positive cost
    G(z) = 1+z*D(z)           # zero or positive gap
    H(z) = 1/(1-z*D(z)*P(z)*G(z))
    T(z) = z*D(z)*H(z)       # nonempty tunes

The completion series are `H` after a duration, `D*H` after a gap, and `G*D*H`
after a step. Strictly preceding layer counts are coefficients of `z*T/(1-z)`;
preceding duration layers use `z*D/(1-z)`. All are rational. Expand each `N/Q`
with `Q[0]=1` using the fixed linear recurrence:

    coefficient[c] = N[c] - sum(Q[j]*coefficient[c-j], j >= 1)

Cache these exact big-integer tables. Find the tune's cost by binary search in
the cumulative table, then subtract completion-count blocks for each component.
Within a duration weight, select its reduced numerator by the existing exact
group counts and binary search. Ranking sums the same preceding blocks.
Neither direction visits previously enumerated tunes.

The six positive integer weights and free-step radius (two semitones) live
together in `nmr/types/tune_count.py`. With radius `k` and tail step cost `s`,
the pitch function is `(2k+1)+2z^s/(1-z^s)`. Free steps form a finite set;
the positive attack cost still keeps each complexity layer finite.
They are design constants, not runtime settings. Changing them or the within-cost
order changes truenames. Do not keep an old/new enumeration toggle or infer which
scheme a truename used. Freeze the selected constants before release.

Small fixtures to verify independently during implementation:

| Tune index | Canonical phrase |
| --- | --- |
| 0 | `@1` |
| 1 | `@1 @1` |
| 2 | `@1 1@1` |
| 3 | `@1 -1@1` |
| 4 | `@1 2@1` |
| 5 | `@1 -2@1` |
| 6 | `@1/2` |
| 7 | `@1 @1 @1` |
| 8 | `@1 @1 1@1` |
| 9 | `@1 @1 -1@1` |
| 359 | `@1/3` |
| 2591 | `@2` |
| 6983144 | `@4` |

## Integration, usability, and limits

Use `tune:` in printed truenames, with internal path `play:music:tune`: add the
`music` category at unused `play` slot 1 and the `tune` leaf at its slot 0.
Parent categories are optional in input and never printed. Existing game paths remain unchanged. The full
prefix removes type-routing cost; shorter scopes use the four-way tree.
There is no separate public rhythm-only type in this work.

Use the same Python codec in the CLI and WebAssembly worker. Add a note/rest
editor, interval entry, rhythmic presets for halves and thirds, and playback.
Keep pitch and duration arithmetic in the shared core; JavaScript handles input,
display, and sound scheduling. Playback tempo and instrument choices must not
affect the encoded result. Staff notation can follow once the exact core and a
usable interval/duration display work; importing arbitrary score files is outside
this plan.

The mathematical pitch domain has no hard interval or octave limit. Playback
devices do. Reject or explain an unrenderable preview without folding pitches
into another octave, truncating the phrase, or changing its truename. A valid tune
index need not yield an attractive tune or one comfortably audible on a device.

Keep mathematical identity separate from operational work limits. Estimate note
count, component sizes, duration-enumeration work, and playback length before
allocating large structures or scheduling sound. A resource refusal must say so;
it must not masquerade as an invalid tune or return a different tune. Publish
tested practical bounds rather than claiming every vocabulary-sized truename can
always be rendered on every device. Avoid silently imposing a new musical limit
that would change the encoded domain.

Canonical decoding remains the default. For supported payloads within work and
capacity limits, browsing can use the identical inverse and return a canonical
result: this leaf needs no many-to-one repair. Broader category browsing retains
the existing redirect rules. Case and whitespace normalization, custom vocabulary
identity, nonrepeating words, and capacity errors follow the existing nmr rules.

## Implementation slices and acceptance

1. Freeze and document the musical identity and enumeration defaults above.
   Update the older plans to identify music as the original goal and remove the
   stale suggestion that transposition equivalence remains undecided. Document
   centered presentation separately from the initial relative-pitch reference.
2. Implement and test exact duration/gap rank and unrank. Start with the table
   above, reduced-fraction equivalence, and rejection of denominators containing
   other primes or more than one factor of three after reduction. Include
   accepted `3/9` and rejected `1/9` and `1/18`. Prove group counts and check
   layer boundaries.
3. Implement phrase normalization and the whole-tune complexity codec. Test the
   initial `@`
   rule, unsigned positive steps, optional later zero steps, transposition,
   octave leaps, rests, ties, repeated attacks, complexity layers, and arbitrary
   index round trips. Empty tunes and all-rest input must fail clearly. Verify that
   optional later zeros normalize to omission without changing a tune's rank.
4. Allocate the leaf and add canonical fixtures for the existing vocabulary,
   custom vocabularies, full and ancestor prefixes, and unprefixed truenames. Keep
   all non-tune type fixtures unchanged; update tune fixtures when tuning the
   pre-release enumeration.
5. Build the editor and playback through the shared browser bridge. Test decoded
   note onsets, ends, and pitches against the exact core events. Sounding right
   by ear is useful review, not a substitute for event-sequence verification.
   Test cumulative-pitch centering, positive and negative rounding including
   exact ties, duration/rest independence, and configurable roots. The example
   must center at two semitones, not at the mean interval of one semitone.
   Changing the presentation root must leave every truename unchanged.
6. Measure truenames for personally meaningful four-, eight-, and sixteen-note
   phrases, with repeated notes, octave leaps, rests, dotted rhythms, and mixed
   binary/ternary subdivisions. Include repeated simple notes, many-note counts,
   large duration weights, capacity boundaries, and explicit resource refusals.
7. Run the repository checks, shared Python/WebAssembly fixtures, and browser UI
   tests where access is available. Commit the final mapping and fixtures before
   describing its truenames as permanent.

Acceptance requires a demonstrated rank/unrank bijection, practical examples of
truename lengths, and input/playback that preserves both melody and rhythm. Do not
claim a six-word bound or replace the exact rhythm with an approximation to meet
an attractive example length.

## Implemented limits, measurements, and verification

The codec refuses work beyond 256 attacked notes, 20,000 input characters,
duration weight 512, total complexity 4,096, or a 4,096-bit tune index. These are
operational bounds, not changes to the mathematical domain. Browser playback additionally requires
20–400 BPM, centered MIDI pitches in 0–127, total length at most 120 seconds,
and individual notes at least 0.01 seconds long. A playback refusal leaves the
normalized phrase available for truename generation.

The editor exposes successive semitone steps, durations, and gaps before notes,
with half/third rhythmic presets. It applies ties explicitly. Absolute-pitch
input is available in `Tune.from_pitches`, which drops initial pitch and leading
silence; there is no performance-file importer or keyboard recorder in this
release. The center and tempo are presentation settings only. Exact bridge
events use strings so JavaScript cannot round large integer pitches or fractions.

Measured test motifs use the pitch pattern
`0,0,7,7,9,9,7,5,5,4,4,2,2,0,7,7`, the duration pattern
`1,1/2,1/2,3/2,1/3,2/3,1,2` repeated, and a third-beat gap before note five.
The first four, eight, and sixteen notes produce these full-prefix payloads:

| Notes | Payload words | Payload |
| --- | --- | --- |
| 4 | 4 | `skip sin basic own` |
| 8 | 10 | `call drop shell john tin bind ran demo poet pen` |
| 16 | 19 | `bid snap rice horn act bra coat was herb sport maui deck bytes had cells folk dies juan away` |

Python tests check independent duration enumeration through weight 24, large
duration indices, initial tune fixtures, arbitrary-index inverses, repeated simple
notes, centering, ties, capacity, and resource refusals. Independent exhaustive
enumeration through cost five checks every index and every within-layer choice
against the rational recurrence. Shared format fixtures
cover all prefix scopes and preserve earlier type names. The WebAssembly smoke
check exercises those fixtures, custom words, exact events, and playback limits.
The browser smoke test includes note editing, play/stop, centering, decode, ties,
and invalid rhythms, but could not run here: headless Chrome failed to launch
and the saved browser access policy denied localhost. Audible and visual browser
verification is outstanding. No musical identity questions remain open.
