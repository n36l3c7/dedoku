"""Unit tests for the basic fish techniques."""

from __future__ import annotations

import unittest

from sudoku_solver import Grid
from sudoku_solver.techniques import XWing


def _restrict_digit_to_columns(
    grid: Grid, digit: int, row_index: int, columns: tuple[int, ...]
) -> None:
    """Remove ``digit`` from every cell of a row outside ``columns``.

    :param grid: The board under construction.
    :type grid: Grid
    :param digit: The digit to restrict.
    :type digit: int
    :param row_index: The row to restrict.
    :type row_index: int
    :param columns: The column indices allowed to keep the digit.
    :type columns: tuple[int, ...]
    """
    for column_index in range(9):
        if column_index not in columns:
            grid.cell(row_index, column_index).remove_candidate(digit)


class XWingTests(unittest.TestCase):
    """Two rows locking a digit into two columns clear those columns."""

    def test_row_based_x_wing(self) -> None:
        """5 locked to columns 1 and 5 in rows 1 and 5 clears the columns."""
        grid = Grid()
        _restrict_digit_to_columns(grid, 5, 0, (0, 4))
        _restrict_digit_to_columns(grid, 5, 4, (0, 4))
        step = XWing().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "X-Wing")
        self.assertGreater(len(step.eliminations), 0)
        for row_index in range(9):
            if row_index in (0, 4):
                continue
            self.assertNotIn(5, grid.cell(row_index, 0).candidates)
            self.assertNotIn(5, grid.cell(row_index, 4).candidates)
        # The four fish corners keep the digit.
        for row_index, column_index in ((0, 0), (0, 4), (4, 0), (4, 4)):
            self.assertIn(5, grid.cell(row_index, column_index).candidates)

    def test_no_pattern_returns_none(self) -> None:
        """An empty board offers no X-Wing."""
        self.assertIsNone(XWing().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
