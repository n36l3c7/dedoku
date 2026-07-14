"""Mass validation of the solving pipeline against a backtracking oracle.

Generates unique-solution puzzles on the fly and solves each one step by
step, verifying every deduction: placements must match the brute-force
solution, eliminations must never remove its digits. Stalls (puzzles the
logic pipeline cannot finish) are counted but are not errors; any unsound
step or unexpected exception is.

Usage::

    python benchmark/validate.py --count 100000 --seed 100 --jobs 8

With ``--jobs`` the work is split into seeded batches across processes,
so large runs scale with the machine. Exits non-zero if any unsound
deduction is found.
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backtracking import solve_backtracking  # noqa: E402
from generate_puzzles import make_puzzle, random_solution  # noqa: E402

from dedoku import Grid, SudokuSolver  # noqa: E402

_CLUE_TARGETS = (17, 17, 24, 28, 32, 40)
"""Clue targets sampled per puzzle; 17 means fully minimal (hardest)."""

_BATCH = 500
"""Puzzles per worker batch when running in parallel."""


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


def run_batch(seed: int, count: int) -> tuple[int, int, list[tuple[str, str]]]:
    """Generate and verify one seeded batch of puzzles.

    :param seed: RNG seed for this batch.
    :type seed: int
    :param count: Number of puzzles to generate and verify.
    :type count: int
    :returns: ``(solved, stalled, failures)`` for the batch, where each
        failure is a ``(puzzle, error)`` pair.
    :rtype: tuple[int, int, list[tuple[str, str]]]
    """
    rng = random.Random(seed)
    solver = SudokuSolver()
    solved = stalled = 0
    failures: list[tuple[str, str]] = []
    for _ in range(count):
        target = rng.choice(_CLUE_TARGETS)
        puzzle = make_puzzle(random_solution(rng), rng, target)
        ok, error = verify(puzzle, solver)
        if error is not None:
            failures.append((puzzle, error))
        elif ok:
            solved += 1
        else:
            stalled += 1
    return solved, stalled, failures


def main() -> int:
    """Run the validation and report a summary.

    :returns: Process exit code — 0 when every deduction was sound.
    :rtype: int
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000,
                        help="number of puzzles to validate")
    parser.add_argument("--seed", type=int, default=7,
                        help="base RNG seed for reproducibility")
    parser.add_argument("--jobs", type=int, default=1,
                        help="worker processes (1 = run in-process)")
    args = parser.parse_args()

    batches = [
        (args.seed * 100_000 + index, min(_BATCH, args.count - index * _BATCH))
        for index in range((args.count + _BATCH - 1) // _BATCH)
    ]
    solved = stalled = done = 0
    failures: list[tuple[str, str]] = []
    start = time.time()

    def absorb(batch_solved: int, batch_stalled: int,
               batch_failures: list[tuple[str, str]], size: int) -> None:
        nonlocal solved, stalled, done
        solved += batch_solved
        stalled += batch_stalled
        done += size
        failures.extend(batch_failures)
        for puzzle, error in batch_failures:
            print(f"UNSOUND: {error}\n  puzzle: {puzzle}", flush=True)
        if done % 5000 < _BATCH:
            print(f"{done}/{args.count} solved={solved} stalled={stalled} "
                  f"unsound={len(failures)} "
                  f"elapsed={time.time() - start:.0f}s", flush=True)

    if args.jobs <= 1:
        for seed, size in batches:
            absorb(*run_batch(seed, size), size)
    else:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = {
                pool.submit(run_batch, seed, size): size
                for seed, size in batches
            }
            for future in as_completed(futures):
                absorb(*future.result(), futures[future])

    print(f"DONE puzzles={args.count} solved={solved} stalled={stalled} "
          f"unsound={len(failures)} elapsed={time.time() - start:.0f}s")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
