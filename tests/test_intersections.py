"""Unit tests for the intersection removal techniques."""

from __future__ import annotations

import unittest

from dedoku import Grid
from dedoku.techniques import ClaimingCandidates, PointingCandidates


class PointingCandidatesTests(unittest.TestCase):
    """A digit confined to one line of a box clears the rest of the line."""

    def test_pointing_triple_clears_rest_of_row(self) -> None:
        """5 confined to row 1 of subgrid 1 strips 5 from R1C4..R1C9."""
        grid = Grid()
        for row_index in (1, 2):
            for column_index in (0, 1, 2):
                grid.cell(row_index, column_index).remove_candidate(5)
        step = PointingCandidates().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "Pointing Candidates")
        self.assertGreater(len(step.eliminations), 0)
        for column_index in range(3, 9):
            self.assertNotIn(5, grid.cell(0, column_index).candidates)
        for column_index in range(3):
            self.assertIn(5, grid.cell(0, column_index).candidates)

    def test_no_pattern_returns_none(self) -> None:
        """An empty board offers no pointing pattern."""
        self.assertIsNone(PointingCandidates().apply(Grid()))


class ClaimingCandidatesTests(unittest.TestCase):
    """A digit confined to one box of a line clears the rest of the box."""

    def test_claiming_clears_rest_of_box(self) -> None:
        """5 confined to subgrid 1 within row 1 strips 5 from the box."""
        grid = Grid()
        for column_index in range(3, 9):
            grid.cell(0, column_index).remove_candidate(5)
        step = ClaimingCandidates().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "Claiming Candidates")
        self.assertGreater(len(step.eliminations), 0)
        for row_index in (1, 2):
            for column_index in (0, 1, 2):
                self.assertNotIn(
                    5, grid.cell(row_index, column_index).candidates
                )
        for column_index in (0, 1, 2):
            self.assertIn(5, grid.cell(0, column_index).candidates)

    def test_no_pattern_returns_none(self) -> None:
        """An empty board offers no claiming pattern."""
        self.assertIsNone(ClaimingCandidates().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
