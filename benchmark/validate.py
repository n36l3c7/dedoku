"""Mass validation of the solving pipeline against a backtracking oracle.

Generates unique-solution puzzles on the fly and solves each one step by
step, verifying every deduction: placements must match the brute-force
solution, eliminations must never remove its digits. Stalls (puzzles the
logic pipeline cannot finish) are counted but are not errors; any unsound
step or unexpected exception is.

Usage::

    python benchmark/validate.py --count 10000 --seed 7

Exits non-zero if any unsound deduction is found.
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backtracking import solve_backtracking  # noqa: E402
from generate_puzzles import make_puzzle, random_solution  # noqa: E402

from dedoku import Grid, SudokuSolver  # noqa: E402

_CLUE_TARGETS = (17, 17, 24, 28, 32, 40)
"""Clue targets sampled per puzzle; 17 means fully minimal (hardest)."""


def verify(puzzle: str, solver: SudokuSolver) -> tuple[bool, str | None]:
    """Solve ``puzzle`` step by step, checking each deduction.

    :param puzzle: The puzzle to solve and verify.
    :type puzzle: str
    :param solver: The solver whose pipeline is exercised.
    :type solver: SudokuSolver
    :returns: ``(solved, error)`` — ``error`` describes the first unsound
        deduction, or is ``None``.
    :rtype: tuple[bool, str | None]
    """
    solution = solve_backtracking(puzzle)
    grid = Grid.from_string(puzzle)
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
                    f"R{row + 1}C{col + 1} against the solution: "
                    f"{step.description}"
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


def main() -> int:
    """Run the validation loop and report a summary.

    :returns: Process exit code — 0 when every deduction was sound.
    :rtype: int
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000,
                        help="number of puzzles to validate")
    parser.add_argument("--seed", type=int, default=7,
                        help="RNG seed for reproducibility")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    solver = SudokuSolver()
    solved = stalled = 0
    failures: list[tuple[str, str]] = []
    start = time.time()
    for index in range(1, args.count + 1):
        target = rng.choice(_CLUE_TARGETS)
        puzzle = make_puzzle(random_solution(rng), rng, target)
        ok, error = verify(puzzle, solver)
        if error is not None:
            failures.append((puzzle, error))
            print(f"UNSOUND: {error}\n  puzzle: {puzzle}", flush=True)
        elif ok:
            solved += 1
        else:
            stalled += 1
        if index % 200 == 0:
            print(f"{index}/{args.count} solved={solved} "
                  f"stalled={stalled} unsound={len(failures)} "
                  f"elapsed={time.time() - start:.0f}s", flush=True)
    print(f"DONE puzzles={args.count} solved={solved} stalled={stalled} "
          f"unsound={len(failures)} elapsed={time.time() - start:.0f}s")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
