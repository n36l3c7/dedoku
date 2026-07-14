"""Uniqueness-based rectangle techniques.

These techniques assume the puzzle has exactly one solution — the standard
convention for published Sudokus. A *deadly pattern* is four unsolved
cells on the corners of a rectangle spanning exactly two subgrids, all
restricted to the same two digits: any solution containing it could swap
the two digits and yield a second solution. A valid puzzle can therefore
never be forced into a deadly pattern, and moves that would create one can
be ruled out.
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING

from .base import Step, Technique

if TYPE_CHECKING:
    from ..grid import Grid

__all__ = ["UniqueRectangle"]


class UniqueRectangle(Technique):
    """Type 1 Unique Rectangle: strip the pair digits off the roof cell.

    When three corners of a two-box rectangle are bivalue cells with the
    same pair ``{a, b}``, the fourth corner (the *roof*) may hold neither
    ``a`` nor ``b``: placing either would force the rectangle into the
    deadly pattern and give the puzzle two solutions.
    """

    name = "Unique Rectangle"

    def apply(self, grid: Grid) -> Step | None:
        """Find the first productive Type 1 unique rectangle.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The eliminations performed, or ``None`` if no productive
            pattern exists.
        :rtype: Step | None
        """
        for row_one, row_two in combinations(range(9), 2):
            for col_one, col_two in combinations(range(9), 2):
                if (row_one // 3 == row_two // 3) == (
                    col_one // 3 == col_two // 3
                ):
                    continue
                corners = (
                    grid.cell(row_one, col_one),
                    grid.cell(row_one, col_two),
                    grid.cell(row_two, col_one),
                    grid.cell(row_two, col_two),
                )
                if any(cell.is_solved for cell in corners):
                    continue
                for roof in corners:
                    floor = [cell for cell in corners if cell is not roof]
                    if not all(cell.is_bivalue for cell in floor):
                        continue
                    if len({cell.candidates for cell in floor}) != 1:
                        continue
                    pair = floor[0].candidates
                    if roof.candidates == pair:
                        continue
                    if not pair & roof.candidates:
                        continue
                    eliminations: list[tuple[int, int, int]] = []
                    for digit in sorted(pair):
                        if roof.remove_candidate(digit):
                            eliminations.append(
                                (roof.row_index, roof.column_index, digit)
                            )
                    pair_text = ", ".join(str(d) for d in sorted(pair))
                    floor_text = ", ".join(cell.label for cell in floor)
                    return Step(
                        technique=self.name,
                        description=(
                            f"unique rectangle on {{{pair_text}}} with "
                            f"floor {floor_text}: {roof.label} can hold "
                            f"neither digit, or the puzzle would have two "
                            f"solutions"
                        ),
                        eliminations=tuple(eliminations),
                    )
        return None
