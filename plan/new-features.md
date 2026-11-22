# A message you can play

**Send a friend a few bars of music that recover the place where you met.** The sender chooses a coordinate, hears its phrase and sends just the score. The recipient enters the notes and gets the same point on the map. They can play it in another key. The reveal works because nmr already assigns the coordinate and the phrase a common integer.

## What the feature would add

Today the library can project a full truename into a Tune, and the browser can display a map, engrave a phrase and play it. The missing interaction is the return trip from a score in someone's hands. Let the recipient enter a short monophonic phrase as pitches, beat durations and rests, audition it, then reveal the object. A beat grid would let someone enter exact rhythm without transcribing interval syntax or having their timing guessed. [Projection API](../nmr/nmr.py) · [Tune identity](../doc/tunes.md) · [Browser displays](../nmr/web/value_display.py)

Use the **full root index** for both directions. A type-relative phrase can require the recipient to know the type in advance, which would spoil the reveal. Rank the entered tune, turn that integer into its root words, then decode canonically. An unassigned index should be reported as such. A different phrase may be a perfectly good message for a different object, so let the recipient replay and edit what they entered.

## Is it worth building?

Try it on paper first. Pick one meaningful date and one coordinate, project each to a score, and give the scores to a musician who has never seen the objects. Can they play one in a different key, preserve its rhythm and recover the expected date or quantized point? Ask whether they would send one back. If the phrases are too long to enjoy playing, that answers the product question before anyone builds an editor.

Additional work beyond the prompt: None.
