"""Almost Locked Set techniques: the ALS-XZ rule.

An *almost locked set* (ALS) is a group of ``n`` unsolved cells inside one
house whose candidates span exactly ``n + 1`` digits — one candidate away
from a naked subset. A single bivalue cell is the smallest ALS.

**ALS-XZ rule.** Take two disjoint ALSs *A* and *B* sharing digits ``x``
and ``z``, where ``x`` is a *restricted common*: every ``x``-cell of *A*
sees every ``x``-cell of *B*, so ``x`` can be placed in at most one of the
two sets. If an outside cell holding ``z`` saw every ``z``-cell of both
sets, ``z`` would vanish from *A* and *B*, locking both and forcing ``x``
into each of them — impossible. Such cells therefore lose ``z``.

This single rule subsumes many named patterns (WXYZ-Wing, Sue-de-Coq and
parts of Death Blossom arise as special cases of small ALS pairs).
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING

from .base import Elimination, Step, Technique

if TYPE_CHECKING:
    from ..grid import Grid

__all__ = ["AlsXz"]

_MAX_ALS_SIZE = 4
"""int: Largest ALS enumerated; bigger sets are rare and costly."""


class AlsXz(Technique):
    """Eliminate through a pair of ALSs joined by a restricted common."""

    name = "ALS-XZ"

    def apply(self, grid: Grid) -> Step | None:
        """Find the first productive ALS-XZ elimination.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The eliminations performed, or ``None`` if no productive
            ALS pair exists.
        :rtype: Step | None
        """
        sets = self._collect(grid)
        for index, (cells_a, cands_a) in enumerate(sets):
            for cells_b, cands_b in sets[index + 1:]:
                if cells_a & cells_b:
                    continue
                common = cands_a & cands_b
                if len(common) < 2:
                    continue
                step = self._match(grid, cells_a, cells_b, common)
                if step is not None:
                    return step
        return None

    @staticmethod
    def _collect(grid: Grid) -> list[tuple[frozenset, frozenset]]:
        """Enumerate every ALS of the board up to the size cap.

        :param grid: The board being searched.
        :type grid: Grid
        :returns: Deduplicated ``(cells, candidates)`` pairs, in a
            deterministic order.
        :rtype: list[tuple[frozenset[Cell], frozenset[int]]]
        """
        seen: set[frozenset] = set()
        sets: list[tuple[frozenset, frozenset]] = []
        for unit in grid.units:
            unsolved = unit.unsolved_cells()
            for size in range(1, min(_MAX_ALS_SIZE, len(unsolved)) + 1):
                for combo in combinations(unsolved, size):
                    cands = frozenset().union(
                        *(cell.candidates for cell in combo)
                    )
                    if len(cands) != size + 1:
                        continue
                    cells = frozenset(combo)
                    if cells in seen:
                        continue
                    seen.add(cells)
                    sets.append((cells, cands))
        return sets

    def _match(
        self,
        grid: Grid,
        cells_a: frozenset,
        cells_b: frozenset,
        common: frozenset,
    ) -> Step | None:
        """Try every restricted common ``x`` and elimination digit ``z``.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :param cells_a: The cells of the first ALS.
        :type cells_a: frozenset[Cell]
        :param cells_b: The cells of the second ALS.
        :type cells_b: frozenset[Cell]
        :param common: The digits shared by both ALSs.
        :type common: frozenset[int]
        :returns: The eliminations performed, or ``None``.
        :rtype: Step | None
        """
        members = cells_a | cells_b
        for x in sorted(common):
            holders_a = [cell for cell in cells_a if x in cell.candidates]
            holders_b = [cell for cell in cells_b if x in cell.candidates]
            if not all(
                first.sees(second)
                for first in holders_a
                for second in holders_b
            ):
                continue
            for z in sorted(common - {x}):
                z_cells = [
                    cell for cell in members if z in cell.candidates
                ]
                eliminations: list[Elimination] = []
                for cell in grid.cells:
                    if cell in members or z not in cell.candidates:
                        continue
                    if all(cell.sees(other) for other in z_cells):
                        cell.remove_candidate(z)
                        eliminations.append(
                            Elimination(cell.row_index, cell.column_index, z)
                        )
                if eliminations:
                    label = lambda cells: ", ".join(  # noqa: E731
                        cell.label
                        for cell in sorted(cells, key=lambda c: c.position)
                    )
                    return Step(
                        technique=self.name,
                        description=(
                            f"ALS-XZ with sets ({label(cells_a)}) and "
                            f"({label(cells_b)}), restricted common {x}: "
                            f"digit {z} is removed from every cell seeing "
                            f"all its homes in both sets"
                        ),
                        eliminations=tuple(eliminations),
                    )
        return None
