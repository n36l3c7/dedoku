"""Unit tests for the 3D Medusa technique."""

from __future__ import annotations

import unittest

from dedoku import Grid
from dedoku.techniques import Medusa3D


class Medusa3DTests(unittest.TestCase):
    """Multi-digit colouring falsifies a self-colliding colour."""

    def test_colour_wrap_across_digits(self) -> None:
        """A chain through digits 1, 2, and 7 collides in column 1.

        Strong links: R1C1 {1,2} (bivalue), row 1 conjugate on 2 to
        R1C6, column 6 conjugate on 2 to R5C6, R5C6 {2,7} (bivalue),
        row 5 conjugate on 7 to R5C1, R5C1 {1,7} (bivalue). The colour
        holding 1 in both R1C1 and R5C1 collides in column 1 and is
        eliminated everywhere.
        """
        grid = Grid()
        for digit in range(1, 10):
            if digit not in (1, 2):
                grid.cell(0, 0).remove_candidate(digit)
            if digit not in (2, 7):
                grid.cell(4, 5).remove_candidate(digit)
            if digit not in (1, 7):
                grid.cell(4, 0).remove_candidate(digit)
        for column_index in range(9):
            if column_index not in (0, 5):
                grid.cell(0, column_index).remove_candidate(2)
                grid.cell(4, column_index).remove_candidate(7)
        for row_index in range(9):
            if row_index not in (0, 4):
                grid.cell(row_index, 5).remove_candidate(2)
        step = Medusa3D().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "3D Medusa")
        self.assertEqual(grid.cell(0, 0).candidates, frozenset({2}))
        self.assertEqual(grid.cell(4, 0).candidates, frozenset({7}))
        self.assertEqual(grid.cell(4, 5).candidates, frozenset({2}))
        self.assertNotIn(2, grid.cell(0, 5).candidates)

    def test_no_pattern_returns_none(self) -> None:
        """An empty board has no strong links at all."""
        self.assertIsNone(Medusa3D().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
