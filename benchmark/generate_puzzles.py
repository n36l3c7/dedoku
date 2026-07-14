"""Generate the benchmark dataset: 500 unique-solution puzzles, 100 per level.

Puzzles are produced by blanking a random complete grid while a solution
counter guarantees uniqueness, then graded by the *hardest technique the
library needs*:

1. ``singles`` — naked/hidden singles only;
2. ``subsets`` — naked/hidden pairs, triples, quads;
3. ``intersections`` — pointing/claiming;
4. ``advanced`` — fish, wings, colouring, uniqueness arguments;
5. ``extreme`` — beyond the original 13 technique families (chains and
   ALS territory, or unsolvable by pure logic).

Grading intentionally runs with the *original 13-family pipeline* so the
levels stay stable as the library grows. The run is reproducible: the RNG
is seeded. Writes ``puzzles_500.csv`` next to this script.
"""

from __future__ import annotations

import csv
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dedoku import Grid, SudokuSolver  # noqa: E402
from dedoku.techniques import (  # noqa: E402
    AvoidableRectangle,
    BivalueUniversalGrave,
    ChuteRemotePairs,
    ClaimingCandidates,
    HiddenPair,
    HiddenQuad,
    HiddenSingle,
    HiddenTriple,
    NakedPair,
    NakedQuad,
    NakedSingle,
    NakedTriple,
    PointingCandidates,
    SimpleColouring,
    Swordfish,
    UniqueRectangle,
    WWing,
    XWing,
    XYZWing,
    YWing,
)

OUTPUT = Path(__file__).resolve().parent / "puzzles_500.csv"
PER_LEVEL = 100
SEED = 42

LEVEL_NAMES = {
    1: "singles",
    2: "subsets",
    3: "intersections",
    4: "advanced",
    5: "extreme",
}

_RANK = {
    "Naked Single": 1, "Hidden Single": 1,
    "Naked Pair": 2, "Hidden Pair": 2, "Naked Triple": 2,
    "Hidden Triple": 2, "Naked Quad": 2, "Hidden Quad": 2,
    "Pointing Candidates": 3, "Claiming Candidates": 3,
}

_GRADING_SOLVER = SudokuSolver((
    NakedSingle(), HiddenSingle(), NakedPair(), HiddenPair(),
    NakedTriple(), HiddenTriple(), NakedQuad(), HiddenQuad(),
    PointingCandidates(), ClaimingCandidates(), XWing(),
    ChuteRemotePairs(), SimpleColouring(), WWing(), YWing(),
    UniqueRectangle(), Swordfish(), XYZWing(),
    BivalueUniversalGrave(), AvoidableRectangle(),
))


def count_solutions(grid: list[int], limit: int = 2) -> int:
    """Count the solutions of a puzzle, stopping at ``limit``.

    :param grid: The board as a list of 81 integers, 0 for empty.
    :type grid: list[int]
    :param limit: Stop counting once this many solutions are found.
    :type limit: int
    :returns: The number of solutions found, capped at ``limit``.
    :rtype: int
    """
    rows = [0] * 9
    cols = [0] * 9
    boxes = [0] * 9
    empties = []
    for index, value in enumerate(grid):
        row, col = divmod(index, 9)
        box = (row // 3) * 3 + col // 3
        if value:
            bit = 1 << value
            if (rows[row] | cols[col] | boxes[box]) & bit:
                return 0
            rows[row] |= bit
            cols[col] |= bit
            boxes[box] |= bit
        else:
            empties.append(index)
    count = 0

    def recurse(unfilled: list[int]) -> bool:
        nonlocal count
        if not unfilled:
            count += 1
            return count < limit
        best_pos = -1
        best_opts: list[int] | None = None
        for pos, index in enumerate(unfilled):
            row, col = divmod(index, 9)
            box = (row // 3) * 3 + col // 3
            used = rows[row] | cols[col] | boxes[box]
            opts = [v for v in range(1, 10) if not used & (1 << v)]
            if best_opts is None or len(opts) < len(best_opts):
                best_opts, best_pos = opts, pos
                if len(opts) <= 1:
                    break
        if not best_opts:
            return True
        index = unfilled[best_pos]
        rest = unfilled[:best_pos] + unfilled[best_pos + 1:]
        row, col = divmod(index, 9)
        box = (row // 3) * 3 + col // 3
        for value in best_opts:
            bit = 1 << value
            rows[row] |= bit
            cols[col] |= bit
            boxes[box] |= bit
            keep_going = recurse(rest)
            rows[row] ^= bit
            cols[col] ^= bit
            boxes[box] ^= bit
            if not keep_going:
                return False
        return True

    recurse(empties)
    return count


def random_solution(rng: random.Random) -> list[int]:
    """Produce a random complete valid grid.

    :param rng: The seeded random generator.
    :type rng: random.Random
    :returns: The board as a list of 81 integers.
    :rtype: list[int]
    """
    grid = [0] * 81
    rows = [0] * 9
    cols = [0] * 9
    boxes = [0] * 9

    def recurse(index: int) -> bool:
        if index == 81:
            return True
        row, col = divmod(index, 9)
        box = (row // 3) * 3 + col // 3
        used = rows[row] | cols[col] | boxes[box]
        values = [v for v in range(1, 10) if not used & (1 << v)]
        rng.shuffle(values)
        for value in values:
            bit = 1 << value
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
    return grid


def make_puzzle(solution: list[int], rng: random.Random,
                target_clues: int) -> str:
    """Blank cells while keeping the solution unique.

    :param solution: A complete valid grid.
    :type solution: list[int]
    :param rng: The seeded random generator.
    :type rng: random.Random
    :param target_clues: Stop once this many clues remain (17 in
        practice means "remove as much as possible").
    :type target_clues: int
    :returns: The puzzle as an 81-character string with ``0`` for blanks.
    :rtype: str
    """
    grid = solution[:]
    order = list(range(81))
    rng.shuffle(order)
    clues = 81
    for index in order:
        if clues <= target_clues:
            break
        saved = grid[index]
        grid[index] = 0
        if count_solutions(grid, 2) == 1:
            clues -= 1
        else:
            grid[index] = saved
    return "".join(map(str, grid))


def grade(puzzle: str) -> tuple[int, str]:
    """Grade a puzzle with the original 13-family pipeline.

    :param puzzle: The puzzle to grade.
    :type puzzle: str
    :returns: The ``(level, hardest technique name)`` pair.
    :rtype: tuple[int, str]
    """
    grid = Grid.from_string(puzzle)
    result = _GRADING_SOLVER.solve(grid)
    if not result.solved:
        return 5, "beyond the base pipeline"
    best_rank, best_name = 1, "given"
    for step in result.steps:
        rank = _RANK.get(step.technique, 4)
        if rank > best_rank:
            best_rank, best_name = rank, step.technique
    return best_rank, best_name


def main() -> None:
    """Fill the five level buckets and write ``puzzles_500.csv``."""
    rng = random.Random(SEED)
    buckets: dict[int, list[tuple[str, int, str]]] = {
        level: [] for level in range(1, 6)
    }
    seen: set[str] = set()
    start = time.time()
    attempts = 0
    while any(len(bucket) < PER_LEVEL for bucket in buckets.values()):
        attempts += 1
        if len(buckets[5]) < PER_LEVEL or len(buckets[4]) < PER_LEVEL:
            target = 17
        elif len(buckets[3]) < PER_LEVEL or len(buckets[2]) < PER_LEVEL:
            target = rng.choice((26, 28, 30, 32))
        else:
            target = rng.choice((36, 38, 40))
        puzzle = make_puzzle(random_solution(rng), rng, target)
        if puzzle in seen:
            continue
        seen.add(puzzle)
        level, hardest = grade(puzzle)
        if len(buckets[level]) < PER_LEVEL:
            clues = sum(1 for ch in puzzle if ch != "0")
            buckets[level].append((puzzle, clues, hardest))
        if attempts % 500 == 0:
            state = {level: len(b) for level, b in buckets.items()}
            print(f"attempts={attempts} "
                  f"elapsed={time.time() - start:.0f}s buckets={state}",
                  flush=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["level", "level_name", "clues", "hardest_technique", "puzzle"]
        )
        for level in range(1, 6):
            for puzzle, clues, hardest in buckets[level]:
                writer.writerow(
                    [level, LEVEL_NAMES[level], clues, hardest, puzzle]
                )
    print(f"done: {OUTPUT} ({attempts} attempts, "
          f"{time.time() - start:.0f}s)")


if __name__ == "__main__":
    main()
