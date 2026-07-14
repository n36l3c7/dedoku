"""Unit tests for the ALS-XZ technique."""

from __future__ import annotations

import unittest

from dedoku import Grid
from dedoku.techniques import AlsXz


class AlsXzTests(unittest.TestCase):
    """Two ALSs with a restricted common digit eliminate the other one."""

    def test_two_cell_als_with_bivalue_als(self) -> None:
        """A = {R1C1, R2C1} on {1,2,3}, B = {R1C5} on {1,3}.

        Digit 1 is the restricted common (R1C1 sees R1C5), so digit 3 is
        removed from every cell seeing both R2C1 (A's 3-home) and R1C5:
        R1C2 and R1C3 (subgrid 1 x row 1) plus R2C4, R2C5, and R2C6
        (row 2 x subgrid 2).
        """
        grid = Grid()
        for digit in range(1, 10):
            if digit not in (1, 2):
                grid.cell(0, 0).remove_candidate(digit)
            if digit not in (2, 3):
                grid.cell(1, 0).remove_candidate(digit)
            if digit not in (1, 3):
                grid.cell(0, 4).remove_candidate(digit)
        step = AlsXz().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "ALS-XZ")
        self.assertEqual(
            set(step.eliminations),
            {(0, 1, 3), (0, 2, 3), (1, 3, 3), (1, 4, 3), (1, 5, 3)},
        )
        for column_index in (3, 4, 5):
            self.assertNotIn(3, grid.cell(1, column_index).candidates)
        # The ALS cells themselves are untouched.
        self.assertEqual(grid.cell(1, 0).candidates, frozenset({2, 3}))
        self.assertEqual(grid.cell(0, 4).candidates, frozenset({1, 3}))

    def test_no_pattern_returns_none(self) -> None:
        """An empty board holds no small almost locked sets."""
        self.assertIsNone(AlsXz().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
