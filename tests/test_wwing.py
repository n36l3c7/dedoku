"""Unit tests for the W-Wing technique."""

from __future__ import annotations

import unittest

from dedoku import Grid
from dedoku.techniques import WWing


class WWingTests(unittest.TestCase):
    """Same-pair cells joined by a strong link eliminate the other digit."""

    def test_w_wing_eliminates_from_common_peers(self) -> None:
        """{1, 2} at R1C1/R5C4 with a strong link on 2 in column 9.

        R1C9 sees R1C1 (row 1) and R5C9 sees R5C4 (row 5), so at least
        one pair cell holds 1: digit 1 is removed from R1C4 and R5C1,
        the only cells seeing both pair cells.
        """
        grid = Grid()
        for digit in range(3, 10):
            grid.cell(0, 0).remove_candidate(digit)
            grid.cell(4, 3).remove_candidate(digit)
        for row_index in range(9):
            if row_index not in (0, 4):
                grid.cell(row_index, 8).remove_candidate(2)
        step = WWing().apply(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique, "W-Wing")
        self.assertEqual(
            set(step.eliminations), {(0, 3, 1), (4, 0, 1)}
        )
        self.assertNotIn(1, grid.cell(0, 3).candidates)
        self.assertNotIn(1, grid.cell(4, 0).candidates)
        # The pair cells keep both candidates.
        self.assertEqual(grid.cell(0, 0).candidates, frozenset({1, 2}))
        self.assertEqual(grid.cell(4, 3).candidates, frozenset({1, 2}))

    def test_no_pattern_returns_none(self) -> None:
        """Without the strong link the pair alone does nothing."""
        grid = Grid()
        for digit in range(3, 10):
            grid.cell(0, 0).remove_candidate(digit)
            grid.cell(4, 3).remove_candidate(digit)
        self.assertIsNone(WWing().apply(grid))
        self.assertIsNone(WWing().apply(Grid()))


if __name__ == "__main__":
    unittest.main()
