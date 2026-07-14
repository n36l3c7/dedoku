dedoku
======

A **pure-Python** Sudoku solving library that relies exclusively on
**human-style logical deduction** — 20 named technique families, from naked
singles to alternating inference chains, and not a single guess.

.. code-block:: bash

   pip install dedoku

.. code-block:: python

   import dedoku

   result = dedoku.solve("530070000600195000098000060800060003400803001"
                         "700020006060000280000419005000080079")
   print(result.solved)   # True
   print(result.grid)     # pretty-printed solved board
   for step in result.steps:
       print(f"[{step.technique}] {step.description}")

**No backtracking. No guessing. Ever.** If the pipeline of logical
techniques cannot finish a puzzle, the solver stops and says so — it never
falls back to trial and error. Every deduction the library makes has been
machine-verified against an independent brute-force oracle (latest run:
5,000 puzzles, zero unsound steps).

.. toctree::
   :maxdepth: 2
   :caption: Contents

   usage
   cli
   techniques
   benchmark
   api
   changelog

Links
-----

- `Source code <https://github.com/n36l3c7/dedoku>`_
- `PyPI project <https://pypi.org/project/dedoku/>`_
- `Issue tracker <https://github.com/n36l3c7/dedoku/issues>`_
