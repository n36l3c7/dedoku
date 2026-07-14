"""Unit tests for the pivot-based wing techniques."""

from __future__ import annotations

import unittest

from sudoku_solver import Grid
from sudoku_solver.techniques import XYZWing, YWing


def _set_candidates(grid: Grid, position: tuple[int, int], keep: set[int]) -> None:
    """Reduce a cell's candidates to exactly ``keep``.

    :param grid: The board under construction.
    :type grid: Grid
    :param position: The ``(row, column)`` position of the cell.
    :type position: tuple[int, int]
    :param keep: The candidates the cell must retain.
    :type keep: set[int]
    """
    for digit in range(1, 10):
        if digit not in keep:
            grid.cell(*position).remove_candidate(digit)


class YWingTests(unittest.TestCase):
    """Pivot {x, y} with pincers {x, z} and {y, z} eliminates z."""

    def test_y_wing_eliminates_shared_digit(self) -> None:
        """Pivot R1C1 {1,2}, pincers R1C5 {1,3} and R5C1 {2,3} kill 3.

        The only cell (other than the pivot) seeing both pincers is
        R5C5, so digit 3 is removed there.
        """
        grid = Grid()
        _set_candidates(grid, (0, 0), {1, 2})
        _set_candidates(grid, (0, 4), {1, 3})
        _set_candidates(grid, (4, 0), {2, 3})
        step = YWing().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "Y-Wing")
        self.assertEqual(step.eliminations, ((4, 4, 3),))
        self.assertNotIn(3, grid.cell(4, 4).candidates)
        # Pattern cells are untouched.
        self.assertEqual(grid.cell(0, 0).candidates, frozenset({1, 2}))
        self.assertEqual(grid.cell(0, 4).candidates, frozenset({1, 3}))
        self.assertEqual(grid.cell(4, 0).candidates, frozenset({2, 3}))

    def test_no_pattern_returns_none(self) -> None:
        """Without a matching pincer pair nothing happens."""
        grid = Grid()
        _set_candidates(grid, (0, 0), {1, 2})
        _set_candidates(grid, (0, 4), {1, 3})
        self.assertIsNone(YWing().apply(grid))
        self.assertIsNone(YWing().apply(Grid()))


class XYZWingTests(unittest.TestCase):
    """Trivalue pivot with two subset pincers eliminates the shared digit."""

    def test_xyz_wing_eliminates_shared_digit(self) -> None:
        """Pivot R1C1 {1,2,3}, pincers R1C5 {1,3} and R3C2 {2,3} kill 3.

        Only R1C2 and R1C3 see the pivot (row 1 and subgrid 1), the row
        pincer (row 1), and the box pincer (subgrid 1), so digit 3 is
        removed exactly there.
        """
        grid = Grid()
        _set_candidates(grid, (0, 0), {1, 2, 3})
        _set_candidates(grid, (0, 4), {1, 3})
        _set_candidates(grid, (2, 1), {2, 3})
        step = XYZWing().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "XYZ-Wing")
        self.assertEqual(
            set(step.eliminations), {(0, 1, 3), (0, 2, 3)}
        )
        self.assertNotIn(3, grid.cell(0, 1).candidates)
        self.assertNotIn(3, grid.cell(0, 2).candidates)
        # Pattern cells are untouched.
        self.assertEqual(grid.cell(0, 0).candidates, frozenset({1, 2, 3}))
        self.assertEqual(grid.cell(0, 4).candidates, frozenset({1, 3}))
        self.assertEqual(grid.cell(2, 1).candidates, frozenset({2, 3}))

    def test_no_pattern_returns_none(self) -> None:
        """Without both pincers nothing happens."""
        grid = Grid()
        _set_candidates(grid, (0, 0), {1, 2, 3})
        _set_candidates(grid, (0, 4), {1, 3})
        self.assertIsNone(XYZWing().apply(grid))
        self.assertIsNone(XYZWing().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
