"""A pure-Python Sudoku solver based on human-style logical deduction.

The package exposes an object-oriented board model (:class:`Cell`,
:class:`Row`, :class:`Column`, :class:`Subgrid`, :class:`Grid`) and a
logic-only solving engine (:class:`SudokuSolver`) that never resorts to
backtracking. It has no external dependencies.

Individual techniques live in :mod:`dedoku.techniques`.
"""

from __future__ import annotations

from .cell import DIGITS, Cell
from .exceptions import ContradictionError, InvalidGridError, SudokuError
from .grid import Grid
from .solver import SolveResult, SudokuSolver
from .techniques import Elimination, Placement, Step, Technique
from .units import Column, Row, Subgrid, Unit

__version__ = "0.6.0"

__all__ = [
    "DIGITS",
    "Cell",
    "Column",
    "ContradictionError",
    "Elimination",
    "Grid",
    "InvalidGridError",
    "Placement",
    "Row",
    "SolveResult",
    "Step",
    "Subgrid",
    "SudokuError",
    "SudokuSolver",
    "Technique",
    "Unit",
    "__version__",
    "solve",
]


def solve(puzzle: str, *, assume_unique: bool = True) -> SolveResult:
    """Solve a puzzle string in one call.

    Convenience wrapper around :class:`Grid` and :class:`SudokuSolver`:
    parses the 81-character puzzle, runs the default logical pipeline,
    and returns the outcome with the final board in ``result.grid``.

    :param puzzle: The puzzle description accepted by
        :meth:`Grid.from_string`.
    :type puzzle: str
    :param assume_unique: When ``False``, uniqueness-based techniques are
        excluded, keeping every deduction sound even if the puzzle might
        have multiple solutions.
    :type assume_unique: bool
    :returns: The session outcome; ``result.grid`` holds the final board
        and ``result.steps`` the full explainable solving path.
    :rtype: SolveResult
    :raises InvalidGridError: If the puzzle description is malformed or
        its givens contradict each other.
    """
    grid = Grid.from_string(puzzle)
    return SudokuSolver(assume_unique=assume_unique).solve(grid)
