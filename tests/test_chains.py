"""Unit tests for the chain techniques."""

from __future__ import annotations

import unittest

from sudoku_solver import Grid
from sudoku_solver.techniques import XChain


def _restrict_digit_to_rows(
    grid: Grid, digit: int, column_index: int, rows: tuple[int, ...]
) -> None:
    """Remove ``digit`` from every cell of a column outside ``rows``.

    :param grid: The board under construction.
    :type grid: Grid
    :param digit: The digit to restrict.
    :type digit: int
    :param column_index: The column to restrict.
    :type column_index: int
    :param rows: The row indices allowed to keep the digit.
    :type rows: tuple[int, ...]
    """
    for row_index in range(9):
        if row_index not in rows:
            grid.cell(row_index, column_index).remove_candidate(digit)


class XChainTests(unittest.TestCase):
    """Alternating single-digit chains pin the digit to an endpoint."""

    def test_skyscraper_shape(self) -> None:
        """Columns 1 and 5 strongly linked on 5, joined through row 8.

        Chain: R1C1 = R8C1 (strong) - R8C5 (weak, row 8) = R2C5 (strong).
        One of R1C1/R2C5 holds 5, so every cell seeing both loses it.
        """
        grid = Grid()
        _restrict_digit_to_rows(grid, 5, 0, (0, 7))
        _restrict_digit_to_rows(grid, 5, 4, (1, 7))
        step = XChain().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "X-Chain")
        self.assertEqual(
            set(step.eliminations),
            {(0, 3, 5), (0, 5, 5), (1, 1, 5), (1, 2, 5)},
        )
        # The chain cells keep the digit.
        for position in ((0, 0), (7, 0), (7, 4), (1, 4)):
            self.assertIn(5, grid.cell(*position).candidates)

    def test_no_pattern_returns_none(self) -> None:
        """An empty board has no conjugate links, hence no chains."""
        self.assertIsNone(XChain().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
