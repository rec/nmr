# Integrate Name, Count, and Clock

## Scope

Replace the three existing views with one page containing three modes: **Name**,
**Count**, and **Clock**, selected by a single group of three radio buttons.
This document is an implementation plan, not authorization to implement it.

Additional work beyond the prompt: None.

## Required interface

- Remove the swap button completely, including its event handling and obsolete
  layout rules. Do not replace it with another direction toggle.
- Keep the page layout fixed across mode changes, editing, conversion, loading,
  errors, playback, and clock ticks. Long content must scroll or wrap inside
  bounded regions without changing their outer dimensions.
- Only the description appears and disappears. Show it only in a mode where it
  can be edited. Reserve its space when hidden so other regions do not move.
  Hidden description controls must be absent from keyboard navigation and the
  accessibility tree.
- Keep a dedicated playback area visible at all times. It contains the true name
  currently playing and the notation for that exact music. Reserve both regions
  even when nothing is playing.
- Add a **Type** menu for restricting iteration to one specific type. Restricted
  iteration plays the short name for that type.
- Keep Increment in Settings with its compact input. Preserve the original large
  count number. Reuse the existing shared volume and tune-rendering settings.

## Proposed fixed layout

Use one persistent page structure, rather than three hidden main elements:

1. Header with Name / Count / Clock radio buttons, Type menu, Settings, and Help.
2. A fixed source region whose value is a name, count, or current time according
   to the selected mode. Keep its position and outer size stable.
3. A reserved description editor region. Proposed visibility: Name mode only.
4. A bounded region for the current value and its existing visual rendering.
5. A fixed playback control row and status region.
6. An always-visible playing-name and music-notation area.

Use stable dimensions within each responsive breakpoint. Mode changes must not
change the page geometry at a given viewport size. On small screens, allow page
scrolling while keeping the same region order and stable sizes. Mode-specific
controls should occupy reserved positions; unavailable controls may be disabled,
but their containers must not collapse. Details of the control row should be
settled before implementation so it does not accumulate duplicate controls.

## Mode behavior

### Name

Support editing a true name and an editable description without swapping panes.
The most recently edited field drives conversion into the other field. Retain
the existing name completion and validation behavior. Prevent programmatic field
updates from triggering conversion loops, and discard stale conversion results.
Confirm this editing model before implementation, as removing Swap leaves the
direction of editing to be defined.

### Count

Retain the exact integer input, positive Increment setting, and existing Run
sequencing. Iterate globally when Type is unrestricted, or within the selected
type when it is restricted. Do not filter global iteration by repeatedly skipping
other types: use the selected type's own enumeration and existing codec logic.
Keep integer arithmetic exact for counts larger than JavaScript's safe integers.
The description editor is hidden; existing non-description value visualizations
remain in their reserved region.

### Clock

Use the current time as the source, retaining the existing interval and time
interpretation settings unless a confirmed decision below replaces them. Keep
the changing current time separate from the snapshot that is actually playing.
Do not let the next clock tick relabel an earlier tune that is still sounding.
The description editor is hidden.

## Type scope and short-name playback

Populate Type from the existing supported type metadata, with an unrestricted
option and concrete types. Reuse the existing scoped encoding/decoding semantics;
do not introduce another enumeration or name format.

For restricted Count iteration, interpret the count in that type's local index
space. Derive the object, short name, audio, and notation from that same scoped
value. Board/card interactions that change the count must also retain that scope.
Keep the selected type visible so the short name has an unambiguous context.

Generate notation from the same tune representation used for playback. Do not
display notation for the global name while playing its short form. Retain
existing work limits and show failures in the fixed status region.

## Shared playback lifecycle

Consolidate the view-specific playback ownership into one page-level owner,
reusing TunePlayer, CountRunner, and the notation renderer where appropriate.
Capture the name, scope, tune, and rendering settings for each playback start.
Update the playing-name and score together when that playback starts, and keep
them tied to its audio clock for highlighting.

Loading or editing the next value must not overwrite the currently playing
snapshot. Stale worker responses must not start music, replace the score, or
advance an obsolete Count run. Define mode/type-change stop behavior before
implementation. When playback ends, keep the area allocated and show an idle
state; confirm whether the last score should remain visible.

## Implementation sequence

1. Resolve the behavior decisions below and agree on the fixed region layout.
2. Replace the view containers and navigation links in `nmr/web/index.html` and
   `navigation.js` with one page and mode radios. Define canonical URL state for
   mode, value, increment, and type; retain Back/Forward and share-link behavior.
   Do not silently add legacy URL migration handling.
3. Adapt `app.js`, `count.js`, and `clock.js` to the shared page and playback
   lifecycle. Remove the old swap and separate-view paths completely.
4. Extend the existing Count bridge operations for scoped enumeration, including
   value actions. Reuse core encoding and decoding rather than duplicating them.
5. Apply the fixed layout in the existing stylesheets and connect the shared
   playback notation and highlighting.
6. Update affected help and README text, including references to Swap, separate
   views, and the removed Highlight switch. Preserve unrelated concurrent edits.
7. Run focused logic tests, required Python checks if Python changes, and browser
   verification. Rebuild `dist/web` before inspecting the local site. Commit and
   push only the integration changes.

## Decisions needed before implementation

- Confirm that description editing is exclusive to Name mode and that both name
  and description can be edited directly there without a direction control.
- Define whether Type affects Name conversion as well as Count iteration.
- Define Type's behavior in Clock mode: limit it to time-compatible types,
  disable it, or give it another explicit meaning. Do not interpret a clock tick
  as an arbitrary type index without agreement. Reconcile this with Clock's
  existing Short name and Time only settings.
- When Type changes, decide whether to reset Count to zero or preserve its numeric
  index in the newly selected scope. These produce different objects.
- Define behavior at the end of a finite type's enumeration: stop or wrap.
- Decide whether mode/type changes stop current audio immediately or allow it to
  finish, and whether returning to Count/Clock resumes automatic playback.
- Decide whether idle playback retains the last score or clears its contents.
- Agree on URL parameter names and whether existing shared links must remain
  supported. The current `type=clock` route must not be confused with Type scope.

## Acceptance checks

- Exactly three mode radios select one mode; no Swap button or old page links
  remain.
- At a fixed viewport size, region bounding boxes remain unchanged across all
  modes, long values, loading, errors, playback, and description visibility.
- Description is visible and keyboard-editable only in the agreed editing mode;
  hiding it leaves its reserved space intact.
- The playback area always exists. Its name, notation, and highlight correspond
  to the audio actually playing, including while the current clock value changes.
- Type-restricted Count traverses only that type, plays the short name, and keeps
  scoped value actions consistent. Test representative finite and unbounded
  types, large indices, increments, and the agreed boundary behavior.
- Switching mode/type during pending conversion or playback cannot resurrect
  stale audio or continue an obsolete iteration.
- Back/Forward, shared links, keyboard mode selection, focus, and compact Settings
  work under the agreed URL and editing contracts.
- Verify desktop and narrow-screen geometry in a browser against freshly built
  assets. Report listening checks separately from automated playback tests.
