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

__all__ = ["UniqueRectangle", "UniqueRectangleType2", "AvoidableRectangle"]


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


class UniqueRectangleType2(Technique):
    """Type 2 Unique Rectangle: the shared extra digit must sit on the roof.

    Two corners of a two-box rectangle (the *floor*) are bivalue cells with
    the same pair ``{a, b}``; the other two corners (the *roof*) hold
    exactly ``{a, b, c}`` with the same extra digit ``c``. If neither roof
    cell were ``c``, all four corners would collapse to the deadly pair
    pattern, so ``c`` occupies one of the roof cells and can be eliminated
    from every other cell that sees them both.
    """

    name = "Unique Rectangle Type 2"

    def apply(self, grid: Grid) -> Step | None:
        """Find the first productive Type 2 unique rectangle.

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
                floor = [cell for cell in corners if cell.is_bivalue]
                roof = [cell for cell in corners if not cell.is_bivalue]
                if len(floor) != 2 or floor[0].candidates != floor[1].candidates:
                    continue
                pair = floor[0].candidates
                extras = {cell.candidates - pair for cell in roof}
                if len(extras) != 1:
                    continue
                extra = next(iter(extras))
                if len(extra) != 1:
                    continue
                if any(not pair < cell.candidates for cell in roof):
                    continue
                digit = next(iter(extra))
                eliminations: list[tuple[int, int, int]] = []
                common = set(roof[0].peers) & set(roof[1].peers)
                for cell in sorted(common, key=lambda c: c.position):
                    if cell in corners:
                        continue
                    if cell.remove_candidate(digit):
                        eliminations.append(
                            (cell.row_index, cell.column_index, digit)
                        )
                if eliminations:
                    pair_text = ", ".join(str(d) for d in sorted(pair))
                    return Step(
                        technique=self.name,
                        description=(
                            f"unique rectangle type 2 on {{{pair_text}}}: "
                            f"digit {digit} must occupy {roof[0].label} or "
                            f"{roof[1].label} to avoid the deadly pattern, "
                            f"so it is removed from every cell seeing both"
                        ),
                        eliminations=tuple(eliminations),
                    )
        return None


class AvoidableRectangle(Technique):
    """Type 1 Avoidable Rectangle: avoid recreating a swappable rectangle.

    Take a two-box rectangle with three corners solved *during solving*
    (none of them givens), where the two corners sharing a line with the
    remaining unsolved corner hold the same digit ``b`` and the diagonal
    corner holds ``a``. If the unsolved corner took ``a``, the four values
    ``a, b / b, a`` could be swapped without touching any given, so the
    puzzle would have a second solution: ``a`` can be eliminated.
    """

    name = "Avoidable Rectangle"

    def apply(self, grid: Grid) -> Step | None:
        """Find the first productive Type 1 avoidable rectangle.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The elimination performed, or ``None`` if no productive
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
                unsolved = [cell for cell in corners if not cell.is_solved]
                if len(unsolved) != 1:
                    continue
                target = unsolved[0]
                solved = [cell for cell in corners if cell is not target]
                if any(cell.is_given for cell in solved):
                    continue
                diagonal = next(
                    cell
                    for cell in solved
                    if cell.row_index != target.row_index
                    and cell.column_index != target.column_index
                )
                sides = [cell for cell in solved if cell is not diagonal]
                if sides[0].value != sides[1].value:
                    continue
                digit = diagonal.value
                assert digit is not None
                if not target.remove_candidate(digit):
                    continue
                return Step(
                    technique=self.name,
                    description=(
                        f"avoidable rectangle: {digit} in {target.label} "
                        f"would let the solved, non-given corners "
                        f"{', '.join(cell.label for cell in solved)} form "
                        f"a swappable rectangle, so the puzzle would have "
                        f"two solutions"
                    ),
                    eliminations=(
                        (target.row_index, target.column_index, digit),
                    ),
                )
        return None
