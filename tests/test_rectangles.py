"""Unit tests for the uniqueness-based rectangle techniques."""

from __future__ import annotations

import unittest

from sudoku_solver import Grid
from sudoku_solver.techniques import UniqueRectangle, UniqueRectangleType2


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


class UniqueRectangleTests(unittest.TestCase):
    """Type 1: three floor pairs strip both digits off the roof."""

    def test_roof_loses_both_pair_digits(self) -> None:
        """Floor {1,2} at R1C1, R1C5, R2C1 clears 1 and 2 from R2C5."""
        grid = Grid()
        _set_candidates(grid, (0, 0), {1, 2})
        _set_candidates(grid, (0, 4), {1, 2})
        _set_candidates(grid, (1, 0), {1, 2})
        _set_candidates(grid, (1, 4), {1, 2, 3})
        step = UniqueRectangle().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "Unique Rectangle")
        self.assertEqual(
            set(step.eliminations), {(1, 4, 1), (1, 4, 2)}
        )
        self.assertEqual(grid.cell(1, 4).candidates, frozenset({3}))

    def test_one_box_rectangle_is_ignored(self) -> None:
        """Corners inside a single subgrid never form a deadly pattern."""
        grid = Grid()
        _set_candidates(grid, (0, 0), {1, 2})
        _set_candidates(grid, (0, 1), {1, 2})
        _set_candidates(grid, (1, 0), {1, 2})
        _set_candidates(grid, (1, 1), {1, 2, 3})
        self.assertIsNone(UniqueRectangle().apply(grid))

    def test_four_box_rectangle_is_ignored(self) -> None:
        """Corners spread over four subgrids never form a deadly pattern."""
        grid = Grid()
        _set_candidates(grid, (0, 0), {1, 2})
        _set_candidates(grid, (0, 4), {1, 2})
        _set_candidates(grid, (4, 0), {1, 2})
        _set_candidates(grid, (4, 4), {1, 2, 3})
        self.assertIsNone(UniqueRectangle().apply(grid))

    def test_no_pattern_returns_none(self) -> None:
        """An empty board offers no unique rectangle."""
        self.assertIsNone(UniqueRectangle().apply(Grid()))


class UniqueRectangleType2Tests(unittest.TestCase):
    """Roof cells sharing one extra digit push it onto the roof line."""

    def test_extra_digit_cleared_from_common_peers(self) -> None:
        """Floor {1,2} with roof {1,2,3} twice strips 3 around the roof."""
        grid = Grid()
        _set_candidates(grid, (0, 0), {1, 2})
        _set_candidates(grid, (0, 4), {1, 2})
        _set_candidates(grid, (1, 0), {1, 2, 3})
        _set_candidates(grid, (1, 4), {1, 2, 3})
        step = UniqueRectangleType2().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "Unique Rectangle Type 2")
        for column_index in (1, 2, 3, 5, 6, 7, 8):
            self.assertNotIn(3, grid.cell(1, column_index).candidates)
        # The roof cells keep the extra digit.
        self.assertIn(3, grid.cell(1, 0).candidates)
        self.assertIn(3, grid.cell(1, 4).candidates)

    def test_different_extras_do_not_match(self) -> None:
        """Roof cells with different extra digits allow no deduction."""
        grid = Grid()
        _set_candidates(grid, (0, 0), {1, 2})
        _set_candidates(grid, (0, 4), {1, 2})
        _set_candidates(grid, (1, 0), {1, 2, 3})
        _set_candidates(grid, (1, 4), {1, 2, 4})
        self.assertIsNone(UniqueRectangleType2().apply(grid))
        self.assertIsNone(UniqueRectangleType2().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
