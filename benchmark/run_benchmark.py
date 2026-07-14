"""Time the backtracking reference against the logic library.

Reads ``puzzles_500.csv``, times both solvers on every puzzle with the
same protocol — puzzle string in, board out, minimum of three runs,
parsing included — and writes ``results.csv`` next to this script.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backtracking import solve_backtracking  # noqa: E402
from sudoku_solver import Grid, SudokuSolver  # noqa: E402

HERE = Path(__file__).resolve().parent
INPUT = HERE / "puzzles_500.csv"
OUTPUT = HERE / "results.csv"
REPS = 3

_SOLVER = SudokuSolver()


def time_backtracking(puzzle: str) -> float:
    """Return the best-of-``REPS`` backtracking time in milliseconds.

    :param puzzle: The puzzle to solve.
    :type puzzle: str
    :returns: The minimum wall-clock time across runs.
    :rtype: float
    """
    best = float("inf")
    for _ in range(REPS):
        start = time.perf_counter()
        solve_backtracking(puzzle)
        best = min(best, time.perf_counter() - start)
    return best * 1000.0


def time_library(puzzle: str) -> tuple[float, bool, str]:
    """Return the best-of-``REPS`` library time in milliseconds.

    :param puzzle: The puzzle to solve.
    :type puzzle: str
    :returns: ``(milliseconds, solved, hardest technique used)``.
    :rtype: tuple[float, bool, str]
    """
    best = float("inf")
    solved = False
    hardest = ""
    for _ in range(REPS):
        start = time.perf_counter()
        grid = Grid.from_string(puzzle)
        result = _SOLVER.solve(grid)
        best = min(best, time.perf_counter() - start)
        solved = result.solved
        hardest = result.techniques_used[-1] if result.steps else "given"
    return best * 1000.0, solved, hardest


def main() -> None:
    """Run the full comparison and write ``results.csv``."""
    with INPUT.open(newline="", encoding="utf-8") as handle:
        puzzles = list(csv.DictReader(handle))
    rows = []
    start = time.time()
    for index, entry in enumerate(puzzles, start=1):
        puzzle = entry["puzzle"]
        bt_ms = time_backtracking(puzzle)
        lib_ms, solved, _ = time_library(puzzle)
        rows.append({
            "id": index,
            "level": entry["level"],
            "level_name": entry["level_name"],
            "clues": entry["clues"],
            "backtracking_ms": f"{bt_ms:.4f}",
            "library_ms": f"{lib_ms:.4f}",
            "library_solved": solved,
            "hardest_technique": entry["hardest_technique"],
            "puzzle": puzzle,
        })
        if index % 100 == 0:
            print(f"{index}/{len(puzzles)} "
                  f"elapsed={time.time() - start:.0f}s", flush=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("written:", OUTPUT)


if __name__ == "__main__":
    main()
