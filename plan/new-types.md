# Possible new types for nmr

## What makes something worth a truename?

Look for things people care about, recognize, and might enjoy giving a lasting
truename. Someone should plausibly want to share the truename, or discover what
their own important thing is called. Practical use is welcome, but sentimental
and playful uses count too.

A home, the place two people met, a wedding color, a favorite melody, or a beloved
chess problem fits. A bank balance does not become interesting merely because we
can encode it. Freezing an arbitrary changing number at a particular instant is
not enough to make it a keepsake.

Prefer candidates with these qualities:

1. **Personal meaning:** there is a convincing answer to “whose favorite thing
   would this be?”
2. **Stable identity:** the same object keeps its truename. Editing a composition or
   choosing a different location creates a different object.
3. **Recognizable decoding:** a friend can see a place, board, color, or pattern,
   or hear a melody. An unexplained identifier is a weaker result.
4. **Compact representation:** the meaningful structure fits in a reasonably
   short truename. A small domain is an advantage, not a requirement.
5. **Clear equality:** we can say precisely when two inputs describe the same
   thing without inventing missing facts or a past history.

This is a candidate list, not authorization to implement everything or reserve
type slots. The proposed homes are conceptual; final allocation needs its own
review against the five-way tree and the root-only last-slot exception.

Additional work beyond the prompt: None.

## Important uses already covered

Do not add a new codec just to put a sentimental label on an existing value.

| Thing someone might want a truename for | Existing representation |
| --- | --- |
| Their home, birthplace, proposal spot, favorite bench, or pet's burial place | A deliberately chosen latitude/longitude point. |
| A birthday, wedding day, adoption day, or another anniversary | Date. |
| An exact birth moment or another precisely known historical instant | Instant, when the timezone or offset is known. |
| A favorite completed game, remembered opening, or unfinished game | Chess or Go move sequence. |
| Their favorite book edition | ISBN, when the edition has one. |
| A personally significant number or fraction | Int or Frac. |

A person's current location changes, but the point identifying their childhood
home does not. The object being encoded is the point, not “where this person lives
now.” Likewise, a date does not need a new Birthday type to become meaningful.
Choosing and explaining these uses may improve the product more than adding
another codec.

## Strong candidates

### 1. Chess position

**Why someone cares:** a favorite endgame, a striking arrangement, the position
from their first win, or a diagram they want to discuss.

**Object:** a board position with side to move and the state needed by the chosen
position semantics, including castling and en passant rights where applicable.
Use FEN as an input format, not as an arbitrary string to encode. The existing
library exposes [position and FEN operations](https://python-chess.readthedocs.io/en/stable/core.html).

Keep the position distinct from the game that reached it. Decide explicitly
whether move counters belong to its identity. Structural validity and proof that
a position is reachable from the initial board are different requirements; do
not promise the latter merely because a position passes validation.

**Assessment:** a strong next addition under `play`. Sparse problems and endgames
may allow shorter truenames than dense boards; measure both before promising lengths.

### 2. Chess problem

**Why someone cares:** “This is the mate-in-two my grandfather showed me,” or a
problem someone composed themselves.

**Object:** a position plus a defined stipulation, initially something narrow
such as direct mate in a specified number of moves. Its solution is not part of
the object unless we deliberately choose to encode a solution separately.

A legal-looking position is not automatically a sound puzzle. Distinguish encoding
a submitted problem from proving that it has a solution or a unique solution.
Browsing must not call an arbitrary generated board a verified puzzle.

**Assessment:** unusually good sentimental and sharing value under `play`, after
position identity is settled. Problem verification is additional work, not an
automatic benefit of the codec.

### 3. Color

**Why someone cares:** a favorite shade, a wedding color, a child's chosen color,
or the precise color used for a personal emblem.

**Object:** start with an opaque color represented by three eight-bit sRGB
components. Hex notation is a convenient input; the reference is the
[W3C definition of sRGB hexadecimal colors](https://www.w3.org/TR/css-color-4/#hex-notation).
Equivalent input spellings should have one truename. Transparency or other color
spaces would need explicitly defined identities.

**Assessment:** especially promising under `play`: compact, immediately visible,
easy to enter, and suitable for browsing. Unlike an arbitrary integer, the value
has a direct sensory interpretation people can care about.

### 4. Short melody or musical motif

**Why someone cares:** a family tune, a few notes from a wedding song, a child's
first composition, or a personal musical signature.

**Object:** a short ordered sequence of pitches, durations, and rests. It truenames
the musical phrase, not a recording, performer, instrument sound, or title.

This is nmr's original motivating purpose, now implemented as `play:music:tune`.
The fixed identity uses successive semitone intervals and exact beat durations;
transposition and playback tempo do not change the truename. Octave distances and
rhythmic scaling do. Presentation centers cumulative pitches around C4 or a
configured root. See `plan/tunes.md` for the enumeration and rhythm domain.

**Assessment:** high appeal under `play`, with length and usability uncertainty.
Start by measuring a few short motifs, not by promising truenames for entire songs.
Decoding should offer notation and playback using the same defined notes.

### 5. Rhythm

**Why someone cares:** a favorite groove, a band's signature beat, a dance
pattern, or a rhythm someone taps to identify themselves.

**Object:** a finite rhythmic phrase or repeating cycle with exact subdivisions,
onsets, and rests. Specify the starting point, whether it loops, and whether
tempo is part of the object. Rotating a cycle must not silently change or preserve
its identity without a deliberate rule.

**Assessment:** promising under `play`, potentially more compact than melody.
A tapped or grid-based input and audible decoding would make the truename useful.

### 6. Instrument tuning

**Why someone cares:** a guitarist's favorite alternate tuning, a family
instrument's tuning, or a tuning used for a particular composition.

**Object:** an ordered set of sounding pitches with a defined string or course
order. Do not depend on an instrument nickname to infer missing pitches. Decide
whether identity is absolute pitches or intervals from a separately specified
reference.

**Assessment:** a compact, plausible enthusiast type under `play`. A dedicated
codec earns its place through musical input, interpretation, and reduced type
overhead compared with a generic list.

### 7. Place-and-time event

**Why someone cares:** a birth, meeting, proposal, wedding, or memorable arrival
at a particular place and moment.

**Object:** a fixed location and a known time, with declared precision. A
date-only event and an event known to the second are not interchangeable. Do
not manufacture midnight or infer a timezone to fill gaps.

The event's title, participants, and story remain outside the encoded value.
The truename identifies the chosen place and time, not a complete biography of what
happened there.

**Assessment:** strong sentimental value under `real`. A fixed domain-specific
combination can omit generic per-item type tags, unlike a list. Measure the
remaining location and time cost; meaningful does not necessarily mean short.

## Further possibilities

| Candidate | Why someone might want a truename | What needs defining first | Assessment |
| --- | --- | --- | --- |
| Go position or problem | A favorite shape, a remembered local fight, or a teaching puzzle. | Board size, stones, side to move, and the meaning of any problem goal. A snapshot alone does not supply the superko history needed for full continuation legality. | Interesting under `play`; keep snapshot identity separate from a historical game state. |
| Color palette | Wedding colors, a personal flag, a room scheme, or a team identity. | Whether order matters and how repeated colors are treated. | Try List of Color first; add a dedicated type only if it improves compactness or semantics. |
| Saved route or trail | A favorite walk, pilgrimage, running loop, or the route of a memorable trip. | Coordinate precision, path direction, and whether different samples of the same curve count as the same route. | Meaningful under `real`, but many points may make truenames impractical. It represents a fixed route, not live journey progress. |
| Geographic area | A garden, family land, a favorite patch of woodland, or a personally drawn boundary. | Boundary representation, precision, and invariance under changing the starting vertex. | A useful extension beyond points under `real`; geometry and length need investigation. |
| Three-dimensional place | A particular upstairs room, studio, or point on a climbing route. | Horizontal and vertical reference systems and precision. | Consider under `real` if two-dimensional coordinates leave a demonstrated need. |
| Annual calendar day | A birthday or anniversary shared without its year. | Month and day only; explicitly handle February 29 without inventing an observance policy. | Modest but practical under `real`; a different domain from a full date. |
| Small geometric or tile pattern | A personal emblem, decorative motif, or favorite symmetric design. | A bounded drawing language or grid and the treatment of rotation and reflection. | Good visual browsing potential under `play`; avoid becoming generic image encoding. |
| Knot or braid diagram | A favorite knot, a design for jewelry, or a mathematical keepsake. | Whether the object is a particular diagram or an equivalence class of diagrams. | Appealing under `pure` or `play`; encoding an underlying knot is a harder identity problem than encoding a drawing. |
| Fractal recipe | A favorite generated image or a personal mathematical signature. | A fixed family, exact parameters, and a permanently defined rendering interpretation. | Exploratory under `pure`; encode the recipe, not arbitrary image bytes. |
| Molecular structure | A chemistry enthusiast's favorite structure or a molecule with personal significance. | Graph identity, stereochemistry, and which chemical distinctions belong to the object. | Exploratory under `pure`; canonicalization complexity needs a convincing payoff. |
| Star or other catalogue object | A favorite star, astronomical object, or natural specimen. | Stable catalogue and entry identity, plus what a decoder can show without external lookup. | Potentially sentimental under `real` or `data`, but another unexplained catalogue number is weak. |
| A specific recording or artwork edition | A wedding recording, favorite performance, or treasured edition. | Whether encoding a catalogue entry, an exact artifact, or the underlying creative work. | Consider a compact stable identifier only when the decoder can explain it. Encoding an identifier does not recover the work itself. |

## Candidates to resist

* Live balances, prices, scores, rankings, ages, weather, or device status. A
  saved snapshot needs a separate reason for someone to care about it.
* Generic strings, arbitrary records, and arbitrary files. These reintroduce the
  removed Text and Record ideas and tend to turn a short description into a much
  longer truename.
* A generic Person type. A person has changing attributes and no single obvious
  immutable representation. Their important dates, places, and creations already
  give us better-defined objects to encode.
* A new Home, Birthday, or FavoriteNumber codec whose value is just an existing
  coordinate, date, or integer. Better examples and presentation may be enough.
* Hashes presented as if decoding them reconstructs a photograph, recording, or
  document. An identifier and the thing it identifies are different objects.
* Catalogue types that assign truenames by today's search order or popularity.
  New entries must not shift existing meanings, and a mutable external service
  must not quietly determine what an established truename means.

## Suggested order of investigation

Start with **Color** and **Chess position**: they offer two different kinds of
appeal, concrete input, and recognizable output. Next investigate **Chess
problem**, **short melody**, and **place-and-time event**. Rhythm and tuning
are good smaller experiments for people with a musical interest.

For each candidate, collect a few examples someone actually cares about. Define
identity, make a minimal rank/unrank experiment, and measure fully prefixed and
unprefixed truename lengths with the existing vocabulary. Check entry and decoding
experience as well as the mathematical mapping. Do not promote a candidate just
because it is straightforward to enumerate.

Canonical encoding remains the default. Browsing should return a valid object
under that type's declared rules and supply its canonical truename. “Valid board,”
“solvable problem,” and “pleasant melody” are different promises; completeness
must not blur them.
