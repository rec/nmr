"""
🔢 ``nmr``: name all canonical things 🔢

Convert each canonical thing into a number, and then that number into a unique,
non-repeating name from a short list of common, short English words... or use a
word list of your choice.

Installs both a module named ``nmr`` and an executable called ``nmr.py``

EXAMPLE
=========

.. code-block:: python

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
"""

from .nmr import Nmr

__all__ = "nmr", "Nmr"

nmr = Nmr()
