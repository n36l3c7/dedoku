"""Unit tests for the chain techniques."""

from __future__ import annotations

import unittest

from sudoku_solver import Grid
from sudoku_solver.techniques import XChain, XYChain


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


class XYChainTests(unittest.TestCase):
    """Bivalue chains eliminate the digit pinned by both endpoints."""

    def test_three_cell_chain(self) -> None:
        """R1C5 {1,3} - R1C1 {1,2} - R5C1 {2,3} pins digit 3.

        Whichever way the chain resolves, R1C5 or R5C1 holds 3, so the
        only outside cell seeing both — R5C5 — loses it.
        """
        grid = Grid()
        for digit in range(1, 10):
            if digit not in (1, 2):
                grid.cell(0, 0).remove_candidate(digit)
            if digit not in (1, 3):
                grid.cell(0, 4).remove_candidate(digit)
            if digit not in (2, 3):
                grid.cell(4, 0).remove_candidate(digit)
        step = XYChain().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "XY-Chain")
        self.assertEqual(step.eliminations, ((4, 4, 3),))
        self.assertNotIn(3, grid.cell(4, 4).candidates)
        # Chain cells are untouched.
        self.assertEqual(grid.cell(0, 0).candidates, frozenset({1, 2}))
        self.assertEqual(grid.cell(0, 4).candidates, frozenset({1, 3}))
        self.assertEqual(grid.cell(4, 0).candidates, frozenset({2, 3}))

    def test_no_pattern_returns_none(self) -> None:
        """An empty board has no bivalue cells, hence no chains."""
        self.assertIsNone(XYChain().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
