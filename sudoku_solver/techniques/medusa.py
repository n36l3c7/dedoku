"""3D Medusa: multi-digit two-colouring of strong links.

Simple colouring works on one digit at a time; 3D Medusa extends the same
idea across digits by also following the strong link inside every bivalue
cell (its two candidates cannot both be false). Colouring the resulting
network splits each component into two colours, exactly one of which is
entirely true.

Deductions implemented:

* **colour wrap (cell)** — two same-coloured candidates inside one cell
  falsify that whole colour;
* **colour wrap (unit)** — two same-coloured candidates of one digit
  sharing a house falsify that whole colour;
* **bicoloured cell** — a cell holding both colours must use one of them,
  so its uncoloured candidates are eliminated;
* **colour trap** — an uncoloured candidate weakly linked to both colours
  can never be placed.
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING

from ..exceptions import ContradictionError
from .base import Step, Technique

if TYPE_CHECKING:
    from ..cell import Cell
    from ..grid import Grid

__all__ = ["Medusa3D"]

_Node = "tuple[Cell, int]"


class Medusa3D(Technique):
    """Eliminate through multi-digit strong-link colouring."""

    name = "3D Medusa"

    def apply(self, grid: Grid) -> Step | None:
        """Colour each strong-link component and apply the Medusa rules.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The eliminations performed, or ``None`` if no component
            yields a deduction.
        :rtype: Step | None
        :raises ContradictionError: If a component contains an odd cycle
            of strong links, which proves the board inconsistent.
        """
        adjacency = self._strong_links(grid)
        visited: set[tuple[Cell, int]] = set()
        for cell in grid.cells:
            for digit in sorted(cell.candidates):
                node = (cell, digit)
                if node not in adjacency or node in visited:
                    continue
                colours = self._colour_component(node, adjacency)
                visited.update(colours)
                if len(colours) < 3:
                    continue
                step = self._wrap(colours)
                if step is None:
                    step = self._trap(grid, colours)
                if step is not None:
                    return step
        return None

    @staticmethod
    def _strong_links(grid: Grid) -> dict:
        """Build the multi-digit strong-link graph of the board.

        Links join the two candidates of a bivalue cell and the two homes
        of every conjugate pair.

        :param grid: The board being searched.
        :type grid: Grid
        :returns: An adjacency mapping between ``(cell, digit)`` nodes.
        :rtype: dict[tuple[Cell, int], list[tuple[Cell, int]]]
        """
        adjacency: dict = {}

        def link(one, two) -> None:
            adjacency.setdefault(one, []).append(two)
            adjacency.setdefault(two, []).append(one)

        for cell in grid.cells:
            if cell.is_bivalue:
                low, high = sorted(cell.candidates)
                link((cell, low), (cell, high))
        for unit in grid.units:
            for digit in sorted(unit.missing_values()):
                homes = unit.cells_with_candidate(digit)
                if len(homes) == 2:
                    link((homes[0], digit), (homes[1], digit))
        return adjacency

    @staticmethod
    def _colour_component(start, adjacency) -> dict:
        """Two-colour the component containing ``start``.

        :param start: Any node of the component.
        :type start: tuple[Cell, int]
        :param adjacency: The strong-link graph.
        :type adjacency: dict
        :returns: A mapping from each component node to colour 0 or 1.
        :rtype: dict[tuple[Cell, int], int]
        :raises ContradictionError: If the component has an odd cycle.
        """
        colours = {start: 0}
        queue = [start]
        while queue:
            node = queue.pop(0)
            for neighbour in adjacency[node]:
                if neighbour not in colours:
                    colours[neighbour] = 1 - colours[node]
                    queue.append(neighbour)
                elif colours[neighbour] == colours[node]:
                    cell, digit = neighbour
                    raise ContradictionError(
                        f"odd strong-link cycle at {cell.label} "
                        f"digit {digit}"
                    )
        return colours

    def _wrap(self, colours: dict) -> Step | None:
        """Falsify a colour that collides with itself.

        :param colours: The two-colouring of one component.
        :type colours: dict[tuple[Cell, int], int]
        :returns: The eliminations performed, or ``None``.
        :rtype: Step | None
        """
        for false_colour in (0, 1):
            group = sorted(
                (node for node, colour in colours.items()
                 if colour == false_colour),
                key=lambda node: (node[0].position, node[1]),
            )
            witness = None
            for (cell_a, digit_a), (cell_b, digit_b) in combinations(group, 2):
                if cell_a is cell_b:
                    witness = (cell_a, digit_a, cell_b, digit_b)
                    break
                if digit_a == digit_b and cell_a.sees(cell_b):
                    witness = (cell_a, digit_a, cell_b, digit_b)
                    break
            if witness is None:
                continue
            eliminations = []
            for cell, digit in group:
                if cell.remove_candidate(digit):
                    eliminations.append(
                        (cell.row_index, cell.column_index, digit)
                    )
            return Step(
                technique=self.name,
                description=(
                    f"3D Medusa: candidates {witness[1]} at "
                    f"{witness[0].label} and {witness[3]} at "
                    f"{witness[2].label} share a colour and exclude each "
                    f"other, so that whole colour is false"
                ),
                eliminations=tuple(eliminations),
            )
        return None

    def _trap(self, grid: Grid, colours: dict) -> Step | None:
        """Eliminate uncoloured candidates constrained by both colours.

        Covers both the bicoloured-cell rule and the classic trap: any
        uncoloured candidate weakly linked to the two colours of the
        component is false, since one of the colours is entirely true.

        :param grid: The board being searched.
        :type grid: Grid
        :param colours: The two-colouring of one component.
        :type colours: dict[tuple[Cell, int], int]
        :returns: The eliminations performed, or ``None``.
        :rtype: Step | None
        """
        eliminations = []
        for cell in grid.cells:
            for digit in sorted(cell.candidates):
                if (cell, digit) in colours:
                    continue
                seen_colours = set()
                for (other, other_digit), colour in colours.items():
                    if other is cell or (
                        other_digit == digit and cell.sees(other)
                    ):
                        seen_colours.add(colour)
                        if len(seen_colours) == 2:
                            break
                if len(seen_colours) == 2:
                    cell.remove_candidate(digit)
                    eliminations.append(
                        (cell.row_index, cell.column_index, digit)
                    )
        if not eliminations:
            return None
        return Step(
            technique=self.name,
            description=(
                "3D Medusa: candidates weakly linked to both colours of "
                "a strong-link component can never be placed"
            ),
            eliminations=tuple(eliminations),
        )
