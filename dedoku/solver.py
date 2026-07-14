"""The solving engine that chains logical techniques.

:class:`SudokuSolver` repeatedly walks an ordered pipeline of techniques,
always retrying from the simplest one after each successful deduction —
exactly how a human solver escalates only when the easy moves dry up.
The engine never guesses: if no technique applies, it stops and reports
a partial result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

from .techniques import (
    AIC,
    AlsXz,
    AvoidableRectangle,
    BivalueUniversalGrave,
    FinnedSwordfish,
    FinnedXWing,
    ChuteRemotePairs,
    ClaimingCandidates,
    HiddenPair,
    HiddenQuad,
    HiddenSingle,
    HiddenTriple,
    Medusa3D,
    NakedPair,
    NakedQuad,
    NakedSingle,
    NakedTriple,
    PointingCandidates,
    SimpleColouring,
    Step,
    Swordfish,
    Technique,
    UniqueRectangle,
    UniqueRectangleType2,
    WWing,
    XChain,
    XWing,
    XYChain,
    XYZWing,
    YWing,
)

if TYPE_CHECKING:
    from .grid import Grid

__all__ = ["SolveResult", "SudokuSolver"]


@dataclass(frozen=True)
class SolveResult:
    """Outcome of a solving session.

    :ivar solved: Whether the puzzle was completely solved.
    :vartype solved: bool
    :ivar steps: Every deduction performed, in order of application.
    :vartype steps: tuple[Step, ...]
    :ivar grid: The board the session worked on, in its final state —
        solved, or holding the partial progress when the pipeline stalled.
    :vartype grid: Grid | None
    """

    solved: bool
    steps: tuple[Step, ...] = field(default=())
    grid: "Grid | None" = field(default=None)

    @property
    def techniques_used(self) -> tuple[str, ...]:
        """tuple[str, ...]: Distinct technique names, in first-use order."""
        return tuple(dict.fromkeys(step.technique for step in self.steps))


class SudokuSolver:
    """Logic-only Sudoku solver (no backtracking, no guessing).

    The solver owns an ordered pipeline of techniques. On every iteration
    it applies the first technique that produces a deduction, then starts
    over from the top of the pipeline, so harder strategies only run when
    the simpler ones are exhausted.

    :param techniques: Custom technique pipeline, tried in the given order.
        When omitted, :meth:`default_techniques` is used.
    :type techniques: Sequence[Technique] | None
    :param assume_unique: When ``False``, uniqueness-based techniques
        (unique rectangles, BUG, avoidable rectangles) are excluded from
        the default pipeline, so solving stays sound on puzzles that may
        have multiple solutions. Ignored when ``techniques`` is given.
    :type assume_unique: bool
    """

    def __init__(
        self,
        techniques: Sequence[Technique] | None = None,
        *,
        assume_unique: bool = True,
    ) -> None:
        self._techniques: tuple[Technique, ...] = (
            tuple(techniques)
            if techniques is not None
            else self.default_techniques(assume_unique=assume_unique)
        )

    @staticmethod
    def default_techniques(*, assume_unique: bool = True) -> tuple[Technique, ...]:
        """Build the default pipeline, ordered from simplest to hardest.

        :param assume_unique: When ``False``, techniques flagged with
            :attr:`~dedoku.techniques.Technique.requires_unique_solution`
            are left out.
        :type assume_unique: bool
        :returns: Fresh instances of the selected techniques.
        :rtype: tuple[Technique, ...]
        """
        pipeline = (
            NakedSingle(),
            HiddenSingle(),
            NakedPair(),
            HiddenPair(),
            NakedTriple(),
            HiddenTriple(),
            NakedQuad(),
            HiddenQuad(),
            PointingCandidates(),
            ClaimingCandidates(),
            XWing(),
            ChuteRemotePairs(),
            SimpleColouring(),
            WWing(),
            YWing(),
            UniqueRectangle(),
            Swordfish(),
            XYZWing(),
            BivalueUniversalGrave(),
            AvoidableRectangle(),
            UniqueRectangleType2(),
            FinnedXWing(),
            FinnedSwordfish(),
            XChain(),
            XYChain(),
            Medusa3D(),
            AlsXz(),
            AIC(),
        )
        if assume_unique:
            return pipeline
        return tuple(
            technique for technique in pipeline
            if not technique.requires_unique_solution
        )

    @property
    def techniques(self) -> tuple[Technique, ...]:
        """tuple[Technique, ...]: The pipeline used by this solver."""
        return self._techniques

    def solve(self, grid: Grid) -> SolveResult:
        """Solve ``grid`` in place as far as pure logic allows.

        The grid is mutated: values are placed and candidates eliminated.
        When the pipeline runs dry before the board is complete, the
        result reports ``solved=False`` and the grid holds the partial
        progress, ready for inspection or for a retry with a stronger
        pipeline.

        :param grid: The board to solve.
        :type grid: Grid
        :returns: The session outcome with the full list of steps.
        :rtype: SolveResult
        :raises dedoku.exceptions.ContradictionError: If the board
            reaches an impossible state, meaning the puzzle has no solution.
        """
        steps: list[Step] = []
        while not grid.is_solved():
            for technique in self._techniques:
                step = technique.apply(grid)
                if step is not None:
                    steps.append(step)
                    break
            else:
                break
        return SolveResult(
            solved=grid.is_solved(), steps=tuple(steps), grid=grid
        )

    def __repr__(self) -> str:
        """Return a debugging representation of the solver.

        :returns: A string listing the pipeline size.
        :rtype: str
        """
        return f"<SudokuSolver with {len(self._techniques)} techniques>"
