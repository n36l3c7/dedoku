"""Unit tests for the Avoidable Rectangle technique."""

from __future__ import annotations

import unittest

from sudoku_solver import Grid
from sudoku_solver.techniques import AvoidableRectangle


class AvoidableRectangleTests(unittest.TestCase):
    """Solved non-given corners forbid completing a swappable rectangle."""

    def test_eliminates_the_diagonal_digit(self) -> None:
        """R1C1=1, R1C5=2, R2C1=2 solved during play strip 1 from R2C5."""
        grid = Grid()
        grid.cell(0, 0).set_value(1)
        grid.cell(0, 4).set_value(2)
        grid.cell(1, 0).set_value(2)
        self.assertIn(1, grid.cell(1, 4).candidates)
        step = AvoidableRectangle().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "Avoidable Rectangle")
        self.assertEqual(step.eliminations, ((1, 4, 1),))
        self.assertNotIn(1, grid.cell(1, 4).candidates)

    def test_givens_never_form_the_pattern(self) -> None:
        """The same corners as puzzle givens allow no deduction."""
        grid = Grid.from_string(
            "100020000"
            "200000000" + "0" * 63
        )
        self.assertTrue(grid.cell(0, 0).is_given)
        self.assertFalse(grid.cell(1, 4).is_given)
        self.assertIsNone(AvoidableRectangle().apply(grid))

    def test_no_pattern_returns_none(self) -> None:
        """An empty board offers no avoidable rectangle."""
        self.assertIsNone(AvoidableRectangle().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
