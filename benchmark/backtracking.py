"""Reference backtracking solver used as the benchmark competitor.

Deliberately the *lightest* classic implementation: bitmask bookkeeping,
cells visited in board order, no heuristics. It exists only to measure the
logic library against brute force — the library itself never guesses.
"""

from __future__ import annotations

__all__ = ["solve_backtracking"]


def solve_backtracking(puzzle: str) -> str:
    """Solve an 81-character puzzle string by plain recursion.

    :param puzzle: The puzzle, ``0`` or ``.`` marking empty cells.
    :type puzzle: str
    :returns: The solved board as an 81-character string.
    :rtype: str
    """
    grid = [int(ch) if ch.isdigit() else 0 for ch in puzzle]
    rows = [0] * 9
    cols = [0] * 9
    boxes = [0] * 9
    for index, value in enumerate(grid):
        if value:
            bit = 1 << value
            row, col = divmod(index, 9)
            rows[row] |= bit
            cols[col] |= bit
            boxes[(row // 3) * 3 + col // 3] |= bit

    def recurse(index: int) -> bool:
        while index < 81 and grid[index]:
            index += 1
        if index == 81:
            return True
        row, col = divmod(index, 9)
        box = (row // 3) * 3 + col // 3
        used = rows[row] | cols[col] | boxes[box]
        for value in range(1, 10):
            bit = 1 << value
            if not used & bit:
                grid[index] = value
                rows[row] |= bit
                cols[col] |= bit
                boxes[box] |= bit
                if recurse(index + 1):
                    return True
                grid[index] = 0
                rows[row] ^= bit
                cols[col] ^= bit
                boxes[box] ^= bit
        return False

    recurse(0)
    return "".join(map(str, grid))
