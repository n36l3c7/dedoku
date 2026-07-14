"""Wing techniques built on a pivot cell: Y-Wing (XY-Wing).

A Y-Wing consists of a bivalue *pivot* ``{x, y}`` seeing two bivalue
*pincers* ``{x, z}`` and ``{y, z}``. Whatever the pivot holds, one of the
pincers is forced to ``z``, so ``z`` can be eliminated from every cell
that sees both pincers.
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING

from .base import Step, Technique

if TYPE_CHECKING:
    from ..grid import Grid

__all__ = ["YWing"]


class YWing(Technique):
    """Eliminate the shared pincer digit of an XY-Wing pattern."""

    name = "Y-Wing"

    def apply(self, grid: Grid) -> Step | None:
        """Find the first productive Y-Wing on the board.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The eliminations performed, or ``None`` if no productive
            pattern exists.
        :rtype: Step | None
        """
        bivalues = [cell for cell in grid.cells if cell.is_bivalue]
        for pivot in bivalues:
            pincer_pool = [
                cell
                for cell in bivalues
                if pivot.sees(cell)
                and cell.candidates != pivot.candidates
                and len(cell.candidates & pivot.candidates) == 1
            ]
            for first, second in combinations(pincer_pool, 2):
                shared = first.candidates & second.candidates
                if len(shared) != 1:
                    continue
                digit = next(iter(shared))
                if digit in pivot.candidates:
                    continue
                if (first.candidates | second.candidates) - shared \
                        != pivot.candidates:
                    continue
                eliminations: list[tuple[int, int, int]] = []
                common = set(first.peers) & set(second.peers)
                for cell in sorted(common, key=lambda c: c.position):
                    if cell.remove_candidate(digit):
                        eliminations.append(
                            (cell.row_index, cell.column_index, digit)
                        )
                if eliminations:
                    return Step(
                        technique=self.name,
                        description=(
                            f"Y-Wing with pivot {pivot.label} and pincers "
                            f"{first.label}, {second.label}: one pincer "
                            f"must hold {digit}, so it is removed from "
                            f"every cell seeing both pincers"
                        ),
                        eliminations=tuple(eliminations),
                    )
        return None
