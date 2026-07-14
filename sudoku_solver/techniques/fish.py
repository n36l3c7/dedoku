"""Basic fish techniques: X-Wing (size 2) and Swordfish (size 3).

A *basic fish* of size ``n`` for a digit is a set of ``n`` base lines
(all rows, or all columns) in which the digit's candidate homes fall into
the same ``n`` cover lines of the perpendicular orientation. The digit must
then occupy the base/cover intersections, so it can be eliminated from the
rest of each cover line.
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING

from .base import Step, Technique

if TYPE_CHECKING:
    from ..cell import Cell
    from ..grid import Grid
    from ..units import Unit

__all__ = ["XWing", "Swordfish"]


class _BasicFish(Technique):
    """Shared implementation for row- and column-based basic fish.

    :cvar size: Number of base lines (2 for X-Wing, 3 for Swordfish).
    """

    size: int = 0

    def apply(self, grid: Grid) -> Step | None:
        """Find the first basic fish that eliminates at least one candidate.

        Row-based fish are searched before column-based fish.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The eliminations performed, or ``None`` if no productive
            fish of this size exists.
        :rtype: Step | None
        """
        for digit in range(1, 10):
            for base_is_row in (True, False):
                step = self._search(grid, digit, base_is_row)
                if step is not None:
                    return step
        return None

    def _search(
        self, grid: Grid, digit: int, base_is_row: bool
    ) -> Step | None:
        """Search one orientation of the fish pattern for one digit.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :param digit: The digit the fish is built on.
        :type digit: int
        :param base_is_row: ``True`` to use rows as base lines and columns
            as cover lines, ``False`` for the transposed search.
        :type base_is_row: bool
        :returns: The eliminations performed, or ``None``.
        :rtype: Step | None
        """
        base_lines: tuple[Unit, ...]
        cover_lines: tuple[Unit, ...]
        if base_is_row:
            base_lines, cover_lines = grid.rows, grid.columns
        else:
            base_lines, cover_lines = grid.columns, grid.rows

        def cover_index(cell: Cell) -> int:
            return cell.column_index if base_is_row else cell.row_index

        candidates: list[tuple[Unit, tuple[Cell, ...]]] = []
        for line in base_lines:
            homes = line.cells_with_candidate(digit)
            if 2 <= len(homes) <= self.size:
                candidates.append((line, homes))
        for chosen in combinations(candidates, self.size):
            covers: set[int] = set()
            for _, homes in chosen:
                covers.update(cover_index(cell) for cell in homes)
            if len(covers) != self.size:
                continue
            base_indices = {line.index for line, _ in chosen}
            eliminations: list[tuple[int, int, int]] = []
            for cover in sorted(covers):
                for cell in cover_lines[cover].cells_with_candidate(digit):
                    base = cell.row_index if base_is_row else cell.column_index
                    if base not in base_indices:
                        cell.remove_candidate(digit)
                        eliminations.append(
                            (cell.row_index, cell.column_index, digit)
                        )
            if eliminations:
                base_kind = "rows" if base_is_row else "columns"
                cover_kind = "columns" if base_is_row else "rows"
                base_text = ", ".join(
                    str(index + 1) for index in sorted(base_indices)
                )
                cover_text = ", ".join(
                    str(index + 1) for index in sorted(covers)
                )
                return Step(
                    technique=self.name,
                    description=(
                        f"digit {digit} in {base_kind} {base_text} is "
                        f"locked into {cover_kind} {cover_text}, so it is "
                        f"removed from the rest of those {cover_kind}"
                    ),
                    eliminations=tuple(eliminations),
                )
        return None


class XWing(_BasicFish):
    """Basic fish of size two."""

    name = "X-Wing"
    size = 2


class Swordfish(_BasicFish):
    """Basic fish of size three.

    Three base lines whose homes for a digit fall into the same three
    cover lines; the base lines need not hold the digit three times each,
    two homes per line are enough.
    """

    name = "Swordfish"
    size = 3
