🔢 `nmr`: name all canonical things 🔢

Give each canonical thing a unique English name using non-repeating words from a
short list of common, short English words... or use a word list of your choice.

The word list is here: https://github.com/rec/nmr/blob/main/words.txt


Canonical things include but are not limited to:

* numbers
* fractions
* times, dates, time intervals
* lat/long positions on the earth
* IP addresses
* UUIDs

Other unimplemented possibilities:

* Phone numbers
* Periodic table
* Chemical compounds(?) (probably not worth the huge effort)
* Pieces of music! (my original motivating example)


Shorter or simpler things should generally be represented by shorter names.

Extending this to your own domain is easy and you can either add it to this
codebase or write your own code and easily plug in in.

Installs both a module named `nmr` and an executable called `nmr.py`

# EXAMPLE

``` python
import nmr

assert nmr(0) == ['the']
assert nmr(2718281828) == ['the', 'race', 'tie', 'hook']

for i in range(-2, 3):
    print(i, ':', *nmr(i))

# Prints
#   -2 : to
#   -1 : of
#   0 : the
#   1 : and
#   2 : a
```

# HOW IT WORKS

All of this involves the same trick over and over again - counting using positional notation:
https://en.wikipedia.org/wiki/Positional_notation

By default `nmr` has 1628 different words, which you can think of as 1628 different
digits.

There's a wrinkle that makes things harder: the author decided that repeating
words was unaesthetic, so counting is a little trickier, but you don't have to
understand how it's done.

With repeating words eliminated, 1628 is the minimum total number of words
needed to be able to represent all 64-bit integers with at most six words.


Conversion runs as follows.

First you take your type, whatever it is, and figure out a way to represent it as a
number in positional notation, where perhaps the digits have different values.

Suppose you're wanting to represent the time of the day, down to milliseconds.

You represent it as a four digit number: hours, minutes, seconds, milliseconds

Next, you take the positional number, and evaluate it into a "type-relative number",
a number that makes sense only within this type.

For example, to represent the time 15:11:55.823, we'd evaluate the number
`((((15 * 60) + 11) * 60 + 55) * 1000 + 823)` to get the type relative number,
but this number might mean something completely different for say, lat-long.

Now, each type also gets its own fixed "type identifier number" and that gets combined
with the type-relative number to give a new number, the `nmr` number which is unique
over all types.

Then that `nmr` number is encoded into a non-repeating sequence of words from the
word list, which is the `nmr` name.

----

In the reverse direction, a `nmr` name is given, and it's converted back into an `nmr`
number, then split into the type identifier number and type-relative number.

The type identifier number is used to look up which type is being decoded, and then
the type-relative number is decoded into the positional number, and finally
back into the original type.

----

You are guaranteed that for each original canonical thing, T, there is a unique
canonical name, and that decoding that name will always reproduce exactly the
same thing.

It's mathematically
an [injection](https://en.wikipedia.org/wiki/Bijection,_injection_and_surjection).

On the other hand, if you start with a random name and try to decode, a data type
isn't required to give any guarantees at all.

You aren't even guaranteed that the decoding will return anything - some names just
won't correspond even to a known type. If a name can be decoded to a known type,
that type decoder might still not be able to come up with a type. Or, if it comes
up with a type, that type might have a different canonical name.

This is all good because it makes it really easy to whip up an encoder/decoder, but for
the basic encoders included with the program, we can offer a better guarantee: that we
can always decode any any type-relative number and return an instance of the type, even
if we weren't given a canonical name.

Separately, we add a "type wrapping" feature to the main program so that unknown type
identifier numbers just wrap repeated over known type identifiers - again, this will
never be a canonical name.

With those features, it means you can type random names into the program, and see what
sort of thing you get.
