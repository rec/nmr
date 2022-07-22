"""
🔢 ``nmbr``: memorable names for large numbers 🔢

Convert an integer, even a very long one, into a short list of common, short
non-repeating English words... or use a word list of your choice.

Installs both a module named ``nmbr`` and an executable called ``nmbr.py``

EXAMPLE
=========

.. code-block:: python

    import nmbr

    assert nmbr(0) == ['the']
    assert nmbr(2718281828) == ['the', 'race', 'tie', 'hook']

    for i in range(-2, 3):
        print(i, ':', *nmbr(i))

    # Prints
    #   -2 : to
    #   -1 : of
    #   0 : the
    #   1 : and
    #   2 : a
"""
__version__ = '0.8.0'

from . nmbr import Nmbr
import sys

nmbr = Nmbr()
nmbr.__dict__.update(globals())

sys.modules[__name__] = nmbr


if __name__ == '__main__':
    from . import __main__

    __main__.main()
