"""Shared test helpers.

Hosts the backtracking *oracle*: an independent brute-force solver used
only to verify the logic library's deductions in tests. It never ships
with the package and is never part of the solving pipeline.
"""

from __future__ import annotations

__all__ = ["solve_backtracking", "verify_with_oracle"]


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


def verify_with_oracle(puzzle: str) -> tuple[bool, str | None]:
    """Solve ``puzzle`` step by step, checking every deduction.

    Each placement must match the true solution and each elimination must
    never remove the true solution's digit. A stall (no technique applies)
    is a legitimate outcome, not an error.

    :param puzzle: The puzzle to solve and verify.
    :type puzzle: str
    :returns: ``(solved, error)`` — ``error`` is ``None`` when every step
        was sound, otherwise a description of the first unsound deduction.
    :rtype: tuple[bool, str | None]
    """
    from dedoku import Grid, SudokuSolver

    solution = solve_backtracking(puzzle)
    grid = Grid.from_string(puzzle)
    solver = SudokuSolver()
    while not grid.is_solved():
        step = None
        for technique in solver.techniques:
            try:
                step = technique.apply(grid)
            except Exception as exc:  # noqa: BLE001 - report, don't crash
                return False, f"{technique.name} raised {exc!r}"
            if step is not None:
                break
        if step is None:
            break
        for row, col, digit in step.placements:
            if solution[row * 9 + col] != str(digit):
                return False, (
                    f"{step.technique} placed {digit} at "
                    f"R{row + 1}C{col + 1}, solution has "
                    f"{solution[row * 9 + col]}: {step.description}"
                )
        for row, col, digit in step.eliminations:
            if solution[row * 9 + col] == str(digit):
                return False, (
                    f"{step.technique} eliminated the true digit {digit} "
                    f"at R{row + 1}C{col + 1}: {step.description}"
                )
    if grid.is_solved() and grid.to_string() != solution:
        return False, "final board differs from the oracle solution"
    return grid.is_solved(), None
