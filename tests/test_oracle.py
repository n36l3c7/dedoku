"""Step-level oracle tests.

Every deduction the pipeline makes is checked against an independent
backtracking solution: placements must match it, eliminations must never
remove its digits. This is the library's core contract — *never deduce a
falsehood* — verified on a sample of benchmark puzzles from every
difficulty level.
"""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

from tests.support import verify_with_oracle

_DATASET = Path(__file__).resolve().parent.parent / "benchmark" / "puzzles_500.csv"
_PER_LEVEL = 10


def _sample() -> list[tuple[str, str]]:
    """Load the first ``_PER_LEVEL`` puzzles of each benchmark level.

    :returns: ``(level, puzzle)`` pairs, or an empty list when the
        benchmark dataset is not available (for example in an sdist).
    :rtype: list[tuple[str, str]]
    """
    if not _DATASET.exists():
        return []
    taken: dict[str, int] = {}
    sample: list[tuple[str, str]] = []
    with _DATASET.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            level = row["level"]
            if taken.get(level, 0) < _PER_LEVEL:
                taken[level] = taken.get(level, 0) + 1
                sample.append((level, row["puzzle"]))
    return sample


@unittest.skipUnless(_DATASET.exists(), "benchmark dataset not available")
class OracleTests(unittest.TestCase):
    """No technique may ever contradict the true solution."""

    def test_every_step_is_sound(self) -> None:
        """Placements match the oracle; eliminations never hit it."""
        sample = _sample()
        self.assertGreater(len(sample), 0)
        for level, puzzle in sample:
            with self.subTest(level=level, puzzle=puzzle[:20] + "..."):
                solved, error = verify_with_oracle(puzzle)
                self.assertIsNone(error)
                if level != "5":
                    self.assertTrue(solved)


if __name__ == "__main__":
    unittest.main()
