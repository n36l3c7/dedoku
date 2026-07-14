Techniques
==========

The default pipeline applies 28 technique instances from 20 families,
ordered from simplest to most advanced; after every successful deduction
it restarts from the top, exactly how a human solver escalates only when
the easy moves dry up. Each module below documents the logic of its
family.

The shared framework classes (:class:`~dedoku.Technique`,
:class:`~dedoku.Step`, :class:`~dedoku.Placement`,
:class:`~dedoku.Elimination`) are documented in the :doc:`api`.

Naked candidates
----------------

.. automodule:: dedoku.techniques.naked
   :members:

Hidden candidates
-----------------

.. automodule:: dedoku.techniques.hidden
   :members:

Intersection removal
--------------------

.. automodule:: dedoku.techniques.intersections
   :members:

Fish (X-Wing, Swordfish, finned variants)
-----------------------------------------

.. automodule:: dedoku.techniques.fish
   :members:

Chute remote pairs
------------------

.. automodule:: dedoku.techniques.chute
   :members:

Simple colouring
----------------

.. automodule:: dedoku.techniques.colouring
   :members:

W-Wing
------

.. automodule:: dedoku.techniques.wwing
   :members:

Wings (Y-Wing, XYZ-Wing)
------------------------

.. automodule:: dedoku.techniques.wings
   :members:

Uniqueness rectangles
---------------------

.. automodule:: dedoku.techniques.rectangles
   :members:

Bivalue universal grave
-----------------------

.. automodule:: dedoku.techniques.bug
   :members:

Single-digit and bivalue chains
-------------------------------

.. automodule:: dedoku.techniques.chains
   :members:

3D Medusa
---------

.. automodule:: dedoku.techniques.medusa
   :members:

Almost locked sets
------------------

.. automodule:: dedoku.techniques.als
   :members:

Alternating inference chains
----------------------------

.. automodule:: dedoku.techniques.aic
   :members:
