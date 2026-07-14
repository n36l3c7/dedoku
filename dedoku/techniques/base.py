"""Framework shared by every logical solving technique.

A technique inspects the board and, when its pattern is found, mutates the
grid (placing a value or eliminating candidates) and reports what it did as
an immutable :class:`Step`. The solver chains these steps until the puzzle
is solved or no technique applies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from ..grid import Grid

__all__ = ["Placement", "Elimination", "Step", "Technique"]


class Placement(NamedTuple):
    """A digit placed at a board position.

    Behaves exactly like the plain ``(row, column, digit)`` tuple it
    replaces — unpacking, indexing, and equality with bare tuples all
    keep working — while adding named field access.

    :ivar row: Zero-based row index (0-8).
    :vartype row: int
    :ivar column: Zero-based column index (0-8).
    :vartype column: int
    :ivar digit: The digit placed, between 1 and 9.
    :vartype digit: int
    """

    row: int
    column: int
    digit: int


class Elimination(NamedTuple):
    """A candidate removed from a board position.

    Behaves exactly like the plain ``(row, column, digit)`` tuple it
    replaces — unpacking, indexing, and equality with bare tuples all
    keep working — while adding named field access.

    :ivar row: Zero-based row index (0-8).
    :vartype row: int
    :ivar column: Zero-based column index (0-8).
    :vartype column: int
    :ivar digit: The candidate removed, between 1 and 9.
    :vartype digit: int
    """

    row: int
    column: int
    digit: int


@dataclass(frozen=True)
class Step:
    """Immutable record of one successful technique application.

    Coordinates are zero-based; the human-readable :attr:`description`
    uses one-based ``RxCy`` labels. Any bare ``(row, column, digit)``
    tuples passed to the constructor are normalised to
    :class:`Placement` / :class:`Elimination` instances.

    :ivar technique: Name of the technique that produced the step.
    :vartype technique: str
    :ivar description: Human-readable explanation of the deduction.
    :vartype description: str
    :ivar placements: Values placed on the board by this step.
    :vartype placements: tuple[Placement, ...]
    :ivar eliminations: Candidates removed from cells by this step.
    :vartype eliminations: tuple[Elimination, ...]
    """

    technique: str
    description: str
    placements: tuple[Placement, ...] = field(default=())
    eliminations: tuple[Elimination, ...] = field(default=())

    def __post_init__(self) -> None:
        """Normalise bare coordinate tuples to their named types."""
        object.__setattr__(
            self, "placements",
            tuple(Placement(*entry) for entry in self.placements),
        )
        object.__setattr__(
            self, "eliminations",
            tuple(Elimination(*entry) for entry in self.eliminations),
        )


class Technique(ABC):
    """Abstract base class for a single logical solving strategy.

    Concrete techniques must be stateless: all information lives in the
    grid, so the same instance can be reused across puzzles.

    :cvar name: Human-readable technique name shown in solving reports.
    :cvar requires_unique_solution: ``True`` for uniqueness-based
        techniques, whose deductions are only sound when the puzzle has
        exactly one solution. The default pipeline can exclude them via
        ``SudokuSolver(assume_unique=False)``.
    """

    name: str = "technique"
    requires_unique_solution: bool = False

    @abstractmethod
    def apply(self, grid: Grid) -> Step | None:
        """Search the grid and apply the first occurrence of the pattern.

        Implementations must mutate the grid **only** when they return a
        step, and each call must perform at most one deduction so that the
        solver can always fall back to the simplest available technique.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: A record of the deduction, or ``None`` if the pattern
            does not occur anywhere on the board.
        :rtype: Step | None
        :raises dedoku.exceptions.ContradictionError: If applying
            the deduction reveals an inconsistent board state.
        """

    def __repr__(self) -> str:
        """Return a debugging representation of the technique.

        :returns: A string such as ``<Technique 'Naked Pair'>``.
        :rtype: str
        """
        return f"<Technique {self.name!r}>"
