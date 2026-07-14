"""Unit tests for the basic fish techniques."""

from __future__ import annotations

import unittest

from sudoku_solver import Grid
from sudoku_solver.techniques import FinnedSwordfish, FinnedXWing, Swordfish, XWing


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


class SwordfishTests(unittest.TestCase):
    """Three rows locking a digit into three columns clear those columns."""

    def test_row_based_swordfish(self) -> None:
        """5 locked to columns 1, 5, 9 across rows 1, 4, 7.

        Row 1 holds 5 only in columns 1 and 5, row 4 only in columns 5
        and 9, row 7 only in columns 1 and 9: a swordfish with two homes
        per base line.
        """
        grid = Grid()
        _restrict_digit_to_columns(grid, 5, 0, (0, 4))
        _restrict_digit_to_columns(grid, 5, 3, (4, 8))
        _restrict_digit_to_columns(grid, 5, 6, (0, 8))
        step = Swordfish().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "Swordfish")
        self.assertGreater(len(step.eliminations), 0)
        for row_index in range(9):
            if row_index in (0, 3, 6):
                continue
            for column_index in (0, 4, 8):
                self.assertNotIn(
                    5, grid.cell(row_index, column_index).candidates
                )
        # The fish cells keep the digit.
        for row_index, column_index in (
            (0, 0), (0, 4), (3, 4), (3, 8), (6, 0), (6, 8),
        ):
            self.assertIn(5, grid.cell(row_index, column_index).candidates)

    def test_no_pattern_returns_none(self) -> None:
        """An empty board offers no swordfish."""
        self.assertIsNone(Swordfish().apply(Grid()))


class FinnedFishTests(unittest.TestCase):
    """Fins confine the extra homes; cover-and-box cells are cleared."""

    def test_finned_x_wing(self) -> None:
        """Rows 1 and 5 on digit 5, columns 1/5, with a fin at R5C6.

        The fin R5C6 shares subgrid 5 with the cover column 5, so 5 is
        removed only from R4C5 and R6C5 — the cover cells inside the fin
        subgrid — while cells outside that box keep the digit.
        """
        grid = Grid()
        _restrict_digit_to_columns(grid, 5, 0, (0, 4))
        _restrict_digit_to_columns(grid, 5, 4, (0, 4, 5))
        step = FinnedXWing().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "Finned X-Wing")
        self.assertEqual(
            set(step.eliminations), {(3, 4, 5), (5, 4, 5)}
        )
        self.assertNotIn(5, grid.cell(3, 4).candidates)
        self.assertNotIn(5, grid.cell(5, 4).candidates)
        # Outside the fin subgrid the cover column keeps the digit.
        self.assertIn(5, grid.cell(2, 4).candidates)
        self.assertIn(5, grid.cell(7, 4).candidates)
        # The fin itself is untouched.
        self.assertIn(5, grid.cell(4, 5).candidates)

    def test_no_pattern_returns_none(self) -> None:
        """An empty board offers no finned fish."""
        self.assertIsNone(FinnedXWing().apply(Grid()))
        self.assertIsNone(FinnedSwordfish().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
