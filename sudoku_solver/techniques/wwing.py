"""W-Wing technique.

Take two bivalue cells with the same candidate pair ``{a, b}`` that share
no house, plus a house in which digit ``b`` has exactly two homes (a strong
link), one home seeing the first pair cell and the other seeing the second.

If neither pair cell held ``a``, both would hold ``b``, and both ends of
the strong link would be blocked — leaving that house with no home for
``b`` at all. Hence at least one pair cell holds ``a``, and ``a`` can be
eliminated from every cell that sees both pair cells.
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING

from .base import Step, Technique

if TYPE_CHECKING:
    from ..grid import Grid

__all__ = ["WWing"]


class WWing(Technique):
    """Eliminate via two same-pair cells joined by a strong link."""

    name = "W-Wing"

    def apply(self, grid: Grid) -> Step | None:
        """Find the first productive W-Wing on the board.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The eliminations performed, or ``None`` if no productive
            pattern exists.
        :rtype: Step | None
        """
        bivalues = [cell for cell in grid.cells if cell.is_bivalue]
        for first, second in combinations(bivalues, 2):
            if first.candidates != second.candidates or first.sees(second):
                continue
            pair = sorted(first.candidates)
            for link_digit, elim_digit in (
                (pair[0], pair[1]),
                (pair[1], pair[0]),
            ):
                for unit in grid.units:
                    homes = unit.cells_with_candidate(link_digit)
                    if len(homes) != 2:
                        continue
                    if any(home in (first, second) for home in homes):
                        continue
                    left, right = homes
                    if not (
                        (left.sees(first) and right.sees(second))
                        or (left.sees(second) and right.sees(first))
                    ):
                        continue
                    eliminations: list[tuple[int, int, int]] = []
                    common = set(first.peers) & set(second.peers)
                    for cell in sorted(common, key=lambda c: c.position):
                        if cell.remove_candidate(elim_digit):
                            eliminations.append(
                                (cell.row_index, cell.column_index, elim_digit)
                            )
                    if eliminations:
                        pair_text = ", ".join(str(d) for d in pair)
                        return Step(
                            technique=self.name,
                            description=(
                                f"W-Wing on pair {{{pair_text}}} at "
                                f"{first.label} and {second.label}, joined "
                                f"by the strong link on digit {link_digit} "
                                f"in {unit.name}: digit {elim_digit} is "
                                f"removed from every cell seeing both"
                            ),
                            eliminations=tuple(eliminations),
                        )
        return None
