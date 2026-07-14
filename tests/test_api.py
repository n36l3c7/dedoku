"""Tests for the public convenience API added for the 1.0 freeze."""

from __future__ import annotations

import unittest

import dedoku
from dedoku import Elimination, Grid, Placement, SudokuSolver
from dedoku.techniques import NakedSingle

EASY_PUZZLE = (
    "530070000"
    "600195000"
    "098000060"
    "800060003"
    "400803001"
    "700020006"
    "060000280"
    "000419005"
    "000080079"
)

EASY_SOLUTION = (
    "534678912"
    "672195348"
    "198342567"
    "859761423"
    "426853791"
    "713924856"
    "961537284"
    "287419635"
    "345286179"
)


class SolveOneLinerTests(unittest.TestCase):
    """dedoku.solve() wraps parsing, solving, and the final board."""

    def test_solves_and_returns_the_grid(self) -> None:
        """The one-liner solves and exposes the board via result.grid."""
        result = dedoku.solve(EASY_PUZZLE)
        self.assertTrue(result.solved)
        self.assertIsNotNone(result.grid)
        assert result.grid is not None
        self.assertEqual(result.grid.to_string(), EASY_SOLUTION)
        self.assertGreater(len(result.steps), 0)

    def test_solver_result_carries_the_same_grid(self) -> None:
        """SudokuSolver.solve() returns the grid it worked on."""
        grid = Grid.from_string(EASY_PUZZLE)
        result = SudokuSolver().solve(grid)
        self.assertIs(result.grid, grid)


class AssumeUniqueTests(unittest.TestCase):
    """assume_unique=False removes the uniqueness-based techniques."""

    def test_default_pipeline_contains_uniqueness_techniques(self) -> None:
        """By default the four uniqueness techniques are present."""
        names = {t.name for t in SudokuSolver().techniques}
        self.assertIn("Unique Rectangle", names)
        self.assertIn("BUG", names)

    def test_flag_excludes_uniqueness_techniques(self) -> None:
        """With the flag off, no technique requires a unique solution."""
        solver = SudokuSolver(assume_unique=False)
        self.assertTrue(
            all(not t.requires_unique_solution for t in solver.techniques)
        )
        names = {t.name for t in solver.techniques}
        for excluded in ("Unique Rectangle", "Unique Rectangle Type 2",
                         "BUG", "Avoidable Rectangle"):
            self.assertNotIn(excluded, names)

    def test_one_liner_forwards_the_flag(self) -> None:
        """The one-liner still solves singles-level puzzles either way."""
        result = dedoku.solve(EASY_PUZZLE, assume_unique=False)
        self.assertTrue(result.solved)


class NamedCoordinateTests(unittest.TestCase):
    """Placements and eliminations expose named fields."""

    def test_placement_fields_and_tuple_compatibility(self) -> None:
        """A placement is both a named record and a plain 3-tuple."""
        grid = Grid()
        cell = grid.cell(4, 4)
        for digit in range(1, 9):
            cell.remove_candidate(digit)
        step = NakedSingle().apply(grid)
        self.assertIsNotNone(step)
        assert step is not None
        placement = step.placements[0]
        self.assertIsInstance(placement, Placement)
        self.assertEqual(placement.row, 4)
        self.assertEqual(placement.column, 4)
        self.assertEqual(placement.digit, 9)
        self.assertEqual(placement, (4, 4, 9))  # backward compatible
        row, column, digit = placement
        self.assertEqual((row, column, digit), (4, 4, 9))

    def test_elimination_fields(self) -> None:
        """Eliminations carry the same named fields."""
        result = dedoku.solve(EASY_PUZZLE)
        eliminations = [
            elimination
            for step in result.steps
            for elimination in step.eliminations
        ]
        for elimination in eliminations:
            self.assertIsInstance(elimination, Elimination)
            self.assertIn(elimination.digit, range(1, 10))


if __name__ == "__main__":
    unittest.main()
