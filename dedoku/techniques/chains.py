"""Chain techniques built on alternating inference.

An inference chain alternates *strong* links ("if this candidate is false,
that one is true") and *weak* links ("if this candidate is true, that one
is false"). A chain that starts and ends with a strong link proves that at
least one of its two endpoints is true, so anything weakly linked to both
endpoints can be eliminated.

This module hosts the single-digit variant (:class:`XChain`, the core of
X-Cycles) and the bivalue-cell variant (:class:`XYChain`). Chains are
found breadth-first, so the shortest productive chain is reported.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from .base import Elimination, Step, Technique

if TYPE_CHECKING:
    from ..cell import Cell
    from ..grid import Grid

__all__ = ["XChain", "XYChain"]

_MAX_LINKS = 12
"""int: Search depth cap; chains longer than this are never useful in
practice and only cost time."""


class XChain(Technique):
    """Single-digit alternating chain (the basic form of X-Cycles).

    Strong links are conjugate pairs (a house with exactly two homes for
    the digit); weak links connect any two homes sharing a house. A chain
    with an odd number of links, starting and ending strongly, pins the
    digit to one of its endpoints: every outside home seeing both
    endpoints is eliminated.
    """

    name = "X-Chain"

    def apply(self, grid: Grid) -> Step | None:
        """Find the shortest productive X-Chain on the board.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The eliminations performed, or ``None`` if no productive
            chain exists.
        :rtype: Step | None
        """
        for digit in range(1, 10):
            nodes = [
                cell for cell in grid.cells
                if not cell.is_solved and digit in cell.candidates
            ]
            if len(nodes) < 4:
                continue
            strong: dict[Cell, list[Cell]] = {cell: [] for cell in nodes}
            for unit in grid.units:
                homes = unit.cells_with_candidate(digit)
                if len(homes) == 2:
                    strong[homes[0]].append(homes[1])
                    strong[homes[1]].append(homes[0])
            weak = {
                cell: [other for other in nodes if cell.sees(other)]
                for cell in nodes
            }
            for origin in nodes:
                if not strong[origin]:
                    continue
                step = self._search(grid, digit, origin, strong, weak)
                if step is not None:
                    return step
        return None

    def _search(
        self,
        grid: Grid,
        digit: int,
        origin: Cell,
        strong: dict[Cell, list[Cell]],
        weak: dict[Cell, list[Cell]],
    ) -> Step | None:
        """Breadth-first search of alternating chains from ``origin``.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :param digit: The digit the chain is built on.
        :type digit: int
        :param origin: The chain's starting home of the digit.
        :type origin: Cell
        :param strong: Conjugate-pair adjacency between homes.
        :type strong: dict[Cell, list[Cell]]
        :param weak: Shared-house adjacency between homes.
        :type weak: dict[Cell, list[Cell]]
        :returns: The eliminations performed, or ``None``.
        :rtype: Step | None
        """
        first = (origin, 0)
        parent: dict[tuple[Cell, int], tuple[Cell, int] | None] = {
            first: None
        }
        queue: deque[tuple[Cell, int]] = deque([first])
        while queue:
            cell, links = queue.popleft()
            if links >= _MAX_LINKS:
                continue
            use_strong = links % 2 == 0
            for nxt in (strong[cell] if use_strong else weak[cell]):
                state = (nxt, links + 1)
                if state in parent:
                    continue
                parent[state] = (cell, links)
                if (links + 1) % 2 == 1 and links + 1 >= 3:
                    step = self._eliminate(
                        digit, origin, nxt, parent, state
                    )
                    if step is not None:
                        return step
                queue.append(state)
        return None

    def _eliminate(
        self,
        digit: int,
        origin: Cell,
        end: Cell,
        parent: dict,
        state: tuple[Cell, int],
    ) -> Step | None:
        """Apply the endpoint rule for one candidate chain.

        :param digit: The digit the chain is built on.
        :type digit: int
        :param origin: One chain endpoint.
        :type origin: Cell
        :param end: The other chain endpoint.
        :type end: Cell
        :param parent: BFS parent pointers used to rebuild the chain.
        :type parent: dict
        :param state: The end state to walk back from.
        :type state: tuple[Cell, int]
        :returns: The eliminations performed, or ``None`` if the chain
            removes nothing.
        :rtype: Step | None
        """
        chain: set[Cell] = set()
        cursor: tuple[Cell, int] | None = state
        while cursor is not None:
            chain.add(cursor[0])
            cursor = parent[cursor]
        eliminations: list[Elimination] = []
        common = set(origin.peers) & set(end.peers)
        for cell in sorted(common, key=lambda c: c.position):
            if cell in chain:
                continue
            if cell.remove_candidate(digit):
                eliminations.append(
                    Elimination(cell.row_index, cell.column_index, digit)
                )
        if not eliminations:
            return None
        return Step(
            technique=self.name,
            description=(
                f"X-Chain on digit {digit} from {origin.label} to "
                f"{end.label} ({state[1]} links): one endpoint holds the "
                f"digit, so it is removed from every cell seeing both"
            ),
            eliminations=tuple(eliminations),
        )


class XYChain(Technique):
    """Chain of bivalue cells whose endpoints pin a shared digit.

    Consecutive cells see each other and hand over one candidate: a cell
    entered on digit ``p`` exits on its other candidate. A chain that
    starts by *leaving* digit ``z`` behind and ends by *producing* ``z``
    proves that one of its endpoints holds ``z``, so ``z`` is eliminated
    from every outside cell seeing both endpoints. Within a single house
    the two-cell case degenerates to a naked pair, so only chains of
    three or more cells are reported.
    """

    name = "XY-Chain"

    def apply(self, grid: Grid) -> Step | None:
        """Find the shortest productive XY-Chain on the board.

        :param grid: The board to inspect and mutate.
        :type grid: Grid
        :returns: The eliminations performed, or ``None`` if no productive
            chain exists.
        :rtype: Step | None
        """
        bivalues = [cell for cell in grid.cells if cell.is_bivalue]
        if len(bivalues) < 3:
            return None
        neighbours = {
            cell: [other for other in bivalues if cell.sees(other)]
            for cell in bivalues
        }
        for digit in range(1, 10):
            for start in bivalues:
                if digit not in start.candidates:
                    continue
                step = self._search(digit, start, neighbours)
                if step is not None:
                    return step
        return None

    def _search(
        self,
        digit: int,
        start: Cell,
        neighbours: dict[Cell, list[Cell]],
    ) -> Step | None:
        """Breadth-first search of XY-Chains from ``start`` pinning ``digit``.

        States are ``(cell, carry)`` pairs, where ``carry`` is the
        candidate the chain hands to the next cell.

        :param digit: The digit both endpoints must pin.
        :type digit: int
        :param start: The chain's first cell, containing ``digit``.
        :type start: Cell
        :param neighbours: Mutual-visibility adjacency between bivalue
            cells.
        :type neighbours: dict[Cell, list[Cell]]
        :returns: The eliminations performed, or ``None``.
        :rtype: Step | None
        """
        carry = next(iter(start.candidates - {digit}))
        first = (start, carry)
        parent: dict[tuple[Cell, int], tuple[Cell, int] | None] = {
            first: None
        }
        queue: deque[tuple[Cell, int]] = deque([first])
        while queue:
            cell, pending = queue.popleft()
            for nxt in neighbours[cell]:
                if pending not in nxt.candidates:
                    continue
                nxt_carry = next(iter(nxt.candidates - {pending}))
                state = (nxt, nxt_carry)
                if state in parent:
                    continue
                parent[state] = (cell, pending)
                if nxt_carry == digit and nxt is not start:
                    step = self._eliminate(digit, start, nxt, parent, state)
                    if step is not None:
                        return step
                queue.append(state)
        return None

    def _eliminate(
        self,
        digit: int,
        start: Cell,
        end: Cell,
        parent: dict,
        state: tuple[Cell, int],
    ) -> Step | None:
        """Apply the endpoint rule for one bivalue chain.

        :param digit: The digit both endpoints pin.
        :type digit: int
        :param start: One chain endpoint.
        :type start: Cell
        :param end: The other chain endpoint.
        :type end: Cell
        :param parent: BFS parent pointers used to rebuild the chain.
        :type parent: dict
        :param state: The end state to walk back from.
        :type state: tuple[Cell, int]
        :returns: The eliminations performed, or ``None`` if the chain
            removes nothing.
        :rtype: Step | None
        """
        chain: set[Cell] = set()
        cursor: tuple[Cell, int] | None = state
        while cursor is not None:
            chain.add(cursor[0])
            cursor = parent[cursor]
        if len(chain) < 3:
            return None
        eliminations: list[Elimination] = []
        common = set(start.peers) & set(end.peers)
        for cell in sorted(common, key=lambda c: c.position):
            if cell in chain:
                continue
            if cell.remove_candidate(digit):
                eliminations.append(
                    Elimination(cell.row_index, cell.column_index, digit)
                )
        if not eliminations:
            return None
        return Step(
            technique=self.name,
            description=(
                f"XY-Chain of {len(chain)} cells from {start.label} to "
                f"{end.label}: one endpoint holds {digit}, so it is "
                f"removed from every cell seeing both"
            ),
            eliminations=tuple(eliminations),
        )
