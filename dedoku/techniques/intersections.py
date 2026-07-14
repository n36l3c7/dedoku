"""Intersection removal techniques: Pointing and Claiming.

Both techniques exploit the three-cell intersection between a subgrid and a
line (row or column):

* **Pointing** — if, inside a subgrid, every home of a digit sits on the
  same line, the digit must occupy that intersection, so it can be removed
  from the rest of the line.
* **Claiming** (box/line reduction) — if, inside a line, every home of a
  digit falls within the same subgrid, the digit is claimed by that box,
  so it can be removed from the box cells outside the line.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Step, Technique

if TYPE_CHECKING:
    from ..grid import Grid

__all__ = ["PointingCandidates", "ClaimingCandidates"]


class PointingCandidates(Technique):
    """Remove a digit from a line when a subgrid confines it to that line."""

    name = "Pointing Candidates"

    def apply(self, grid: Grid) -> Step | None:
        """Find the first pointing pair/triple that eliminates a candidate.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The eliminations performed, or ``None`` if no productive
            pointing pattern exists.
        :rtype: Step | None
        """
        for subgrid in grid.subgrids:
            for digit in sorted(subgrid.missing_values()):
                homes = subgrid.cells_with_candidate(digit)
                if not 2 <= len(homes) <= 3:
                    continue
                if len({cell.row_index for cell in homes}) == 1:
                    line = homes[0].row
                elif len({cell.column_index for cell in homes}) == 1:
                    line = homes[0].column
                else:
                    continue
                eliminations: list[tuple[int, int, int]] = []
                for cell in line.cells_with_candidate(digit):
                    if cell.subgrid is not subgrid:
                        cell.remove_candidate(digit)
                        eliminations.append(
                            (cell.row_index, cell.column_index, digit)
                        )
                if eliminations:
                    return Step(
                        technique=self.name,
                        description=(
                            f"in {subgrid.name}, digit {digit} is confined "
                            f"to {line.name}, so it is removed from the "
                            f"rest of the line"
                        ),
                        eliminations=tuple(eliminations),
                    )
        return None


class ClaimingCandidates(Technique):
    """Remove a digit from a subgrid when a line confines it to that box."""

    name = "Claiming Candidates"

    def apply(self, grid: Grid) -> Step | None:
        """Find the first claiming (box/line) reduction on the board.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The eliminations performed, or ``None`` if no productive
            claiming pattern exists.
        :rtype: Step | None
        """
        for line in grid.rows + grid.columns:
            for digit in sorted(line.missing_values()):
                homes = line.cells_with_candidate(digit)
                if not 2 <= len(homes) <= 3:
                    continue
                if len({cell.subgrid.index for cell in homes}) != 1:
                    continue
                subgrid = homes[0].subgrid
                members = set(homes)
                eliminations: list[tuple[int, int, int]] = []
                for cell in subgrid.cells_with_candidate(digit):
                    if cell not in members:
                        cell.remove_candidate(digit)
                        eliminations.append(
                            (cell.row_index, cell.column_index, digit)
                        )
                if eliminations:
                    return Step(
                        technique=self.name,
                        description=(
                            f"in {line.name}, digit {digit} is confined to "
                            f"{subgrid.name}, so it is removed from the "
                            f"rest of the box"
                        ),
                        eliminations=tuple(eliminations),
                    )
        return None
