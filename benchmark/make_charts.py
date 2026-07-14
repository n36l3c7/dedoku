"""Render the README benchmark charts as static SVG files.

Reads ``results.csv`` and writes four self-contained SVGs into ``docs/``:
a solve-time distribution strip plot and a technique-usage bar chart,
each in a light and a dark variant (the README swaps them with a
``<picture>`` element). Standard library only.
"""

from __future__ import annotations

import csv
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dedoku import Grid, SudokuSolver  # noqa: E402

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent / "docs"

THEMES = {
    "light": {
        "surface": "#fcfcfb", "ink": "#0b0b0b", "secondary": "#52514e",
        "muted": "#898781", "grid": "#e1e0d9", "baseline": "#c3c2b7",
        "bt": "#2a78d6", "lib": "#1baf7a",
    },
    "dark": {
        "surface": "#1a1a19", "ink": "#ffffff", "secondary": "#c3c2b7",
        "muted": "#898781", "grid": "#2c2c2a", "baseline": "#383835",
        "bt": "#3987e5", "lib": "#199e70",
    },
}
FONT = "system-ui, -apple-system, Segoe UI, sans-serif"
LEVELS = [
    (1, "Singles"), (2, "Subsets"), (3, "Intersections"),
    (4, "Advanced"), (5, "Extreme"),
]
T_MIN, T_MAX = 0.05, 3000.0


def median(values: list[float]) -> float:
    """Return the median of a non-empty list.

    :param values: The sample.
    :type values: list[float]
    :returns: The median value.
    :rtype: float
    """
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def jitter(seed: int) -> float:
    """Deterministic pseudo-random offset in [-0.5, 0.5).

    :param seed: Any integer; the same seed gives the same offset.
    :type seed: int
    :returns: The offset.
    :rtype: float
    """
    value = seed * 2654435761 % 4294967296
    value = (value ^ (value >> 13)) * 1274126177 % 4294967296
    return ((value >> 8) % 1000) / 1000 - 0.5


def _text(x: float, y: float, content: str, fill: str, size: float,
          anchor: str = "start", weight: str = "400") -> str:
    """Build an SVG text element.

    :param x: X position.
    :type x: float
    :param y: Y position.
    :type y: float
    :param content: The text content.
    :type content: str
    :param fill: The text colour.
    :type fill: str
    :param size: Font size in pixels.
    :type size: float
    :param anchor: The text-anchor value.
    :type anchor: str
    :param weight: The font weight.
    :type weight: str
    :returns: The SVG fragment.
    :rtype: str
    """
    return (f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" '
            f'font-size="{size}" font-family="{FONT}" '
            f'text-anchor="{anchor}" font-weight="{weight}">'
            f"{content}</text>")


def distribution_chart(rows: list[dict], theme: dict) -> str:
    """Render the per-level solve-time strip plot.

    :param rows: The parsed ``results.csv`` rows.
    :type rows: list[dict]
    :param theme: The colour tokens to use.
    :type theme: dict
    :returns: The complete SVG document.
    :rtype: str
    """
    width, m_left, m_right, m_top, m_bottom = 940, 140, 95, 48, 38
    plot_w = width - m_left - m_right
    row_h, row_gap, group_gap = 22, 4, 16
    group_h = row_h * 2 + row_gap
    plot_h = len(LEVELS) * group_h + (len(LEVELS) - 1) * group_gap
    height = m_top + plot_h + m_bottom

    def x(t: float) -> float:
        t = min(max(t, T_MIN), T_MAX)
        span = math.log10(T_MAX) - math.log10(T_MIN)
        return m_left + (math.log10(t) - math.log10(T_MIN)) / span * plot_w

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
        f'{height}" width="{width}" height="{height}" role="img" '
        f'aria-label="Solve-time distribution by difficulty level">',
        f'<rect width="{width}" height="{height}" rx="8" '
        f'fill="{theme["surface"]}"/>',
    ]
    for tick in (0.1, 1, 10, 100, 1000):
        gx = x(tick)
        parts.append(
            f'<line x1="{gx:.1f}" y1="{m_top}" x2="{gx:.1f}" '
            f'y2="{m_top + plot_h}" stroke="{theme["grid"]}" '
            f'stroke-width="1"/>'
        )
        label = "1,000" if tick >= 1000 else str(tick)
        parts.append(_text(gx, m_top + plot_h + 18, label,
                           theme["muted"], 11, "middle"))
    parts.append(_text(m_left + plot_w, m_top + plot_h + 32,
                       "solve time, ms (log scale)",
                       theme["muted"], 11, "end"))
    # legend
    for offset, (key, label) in enumerate(
        (("bt", "Backtracking"), ("lib", "Logic library"))
    ):
        lx = m_left + offset * 150
        parts.append(f'<circle cx="{lx}" cy="22" r="5" '
                     f'fill="{theme[key]}"/>')
        parts.append(_text(lx + 11, 26, label, theme["secondary"], 12.5))

    by_level: dict[str, list[dict]] = {}
    for row in rows:
        by_level.setdefault(row["level"], []).append(row)
    for group_index, (level, name) in enumerate(LEVELS):
        gy = m_top + group_index * (group_h + group_gap)
        parts.append(_text(m_left - 14, gy + group_h / 2 - 3,
                           f"Level {level}", theme["ink"], 12.5,
                           "end", "600"))
        parts.append(_text(m_left - 14, gy + group_h / 2 + 13, name,
                           theme["secondary"], 11.5, "end"))
        group = by_level[str(level)]
        for series_index, key in enumerate(("bt", "lib")):
            column = "backtracking_ms" if key == "bt" else "library_ms"
            row_y = gy + series_index * (row_h + row_gap) + row_h / 2
            values = []
            for row in group:
                value = float(row[column])
                values.append(value)
                cy = row_y + jitter(int(row["id"]) * 2 + series_index) \
                    * (row_h - 9)
                parts.append(
                    f'<circle cx="{x(value):.1f}" cy="{cy:.1f}" r="3.5" '
                    f'fill="{theme[key]}" fill-opacity="0.55" '
                    f'stroke="{theme["surface"]}" stroke-width="1"/>'
                )
            med = median(values)
            parts.append(
                f'<rect x="{x(med) - 1.5:.1f}" y="{row_y - row_h / 2 + 1:.1f}" '
                f'width="3" height="{row_h - 2}" fill="{theme[key]}" '
                f'stroke="{theme["surface"]}" stroke-width="1"/>'
            )
            digits = 1 if med < 100 else 0
            parts.append(_text(m_left + plot_w + 12, row_y + 4,
                               f"med {med:.{digits}f}",
                               theme["secondary"], 11.5))
    parts.append("</svg>")
    return "".join(parts)


def usage_chart(theme: dict, usage: list[tuple[str, int]],
                solved: int) -> str:
    """Render the technique-usage bar chart for the extreme level.

    :param theme: The colour tokens to use.
    :type theme: dict
    :param usage: ``(technique, puzzles)`` pairs, sorted descending.
    :type usage: list[tuple[str, int]]
    :param solved: How many extreme puzzles the library solved.
    :type solved: int
    :returns: The complete SVG document.
    :rtype: str
    """
    width, m_left, m_right, m_top, m_bottom = 760, 190, 70, 18, 40
    bar_h, bar_gap = 14, 12
    plot_w = width - m_left - m_right
    height = m_top + len(usage) * (bar_h + bar_gap) - bar_gap + m_bottom
    top = max(count for _, count in usage)
    scale_max = math.ceil(top / 20) * 20

    def x(value: float) -> float:
        return m_left + value / scale_max * plot_w

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
        f'{height}" width="{width}" height="{height}" role="img" '
        f'aria-label="Technique usage on solved extreme puzzles">',
        f'<rect width="{width}" height="{height}" rx="8" '
        f'fill="{theme["surface"]}"/>',
    ]
    plot_bottom = m_top + len(usage) * (bar_h + bar_gap) - bar_gap
    for tick in range(0, scale_max + 1, 20):
        gx = x(tick)
        parts.append(
            f'<line x1="{gx:.1f}" y1="{m_top}" x2="{gx:.1f}" '
            f'y2="{plot_bottom}" stroke="{theme["grid"]}" '
            f'stroke-width="1"/>'
        )
        parts.append(_text(gx, plot_bottom + 16, str(tick),
                           theme["muted"], 11, "middle"))
    parts.append(_text(m_left + plot_w, plot_bottom + 31,
                       f"solved extreme puzzles using the technique "
                       f"(of {solved})", theme["muted"], 11, "end"))
    for index, (technique, count) in enumerate(usage):
        y = m_top + index * (bar_h + bar_gap)
        bar_w = x(count) - m_left
        parts.append(
            f'<rect x="{m_left}" y="{y}" width="{bar_w:.1f}" '
            f'height="{bar_h}" rx="4" fill="{theme["bt"]}"/>'
        )
        if bar_w > 8:  # square the baseline end
            parts.append(
                f'<rect x="{m_left}" y="{y}" width="6" height="{bar_h}" '
                f'fill="{theme["bt"]}"/>'
            )
        parts.append(_text(m_left - 10, y + bar_h - 3, technique,
                           theme["ink"], 12, "end"))
        parts.append(_text(m_left + bar_w + 8, y + bar_h - 3, str(count),
                           theme["secondary"], 11.5))
    parts.append(
        f'<line x1="{m_left}" y1="{m_top}" x2="{m_left}" '
        f'y2="{plot_bottom}" stroke="{theme["baseline"]}" '
        f'stroke-width="1"/>'
    )
    parts.append("</svg>")
    return "".join(parts)


def collect_usage(rows: list[dict]) -> tuple[list[tuple[str, int]], int]:
    """Re-solve the extreme puzzles and count advanced-technique usage.

    :param rows: The parsed ``results.csv`` rows.
    :type rows: list[dict]
    :returns: Sorted ``(technique, count)`` pairs and the solved count.
    :rtype: tuple[list[tuple[str, int]], int]
    """
    advanced = {
        "Unique Rectangle Type 2", "Finned X-Wing", "Finned Swordfish",
        "X-Chain", "XY-Chain", "3D Medusa", "ALS-XZ", "AIC",
    }
    solver = SudokuSolver()
    counter: Counter[str] = Counter()
    solved = 0
    for row in rows:
        if row["level"] != "5":
            continue
        grid = Grid.from_string(row["puzzle"])
        result = solver.solve(grid)
        if result.solved:
            solved += 1
            used = {
                step.technique for step in result.steps
                if step.technique in advanced
            }
            counter.update(used)
    return counter.most_common(), solved


def main() -> None:
    """Render all four SVG files into ``docs/``."""
    DOCS.mkdir(exist_ok=True)
    with (HERE / "results.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    usage, solved = collect_usage(rows)
    for name, theme in THEMES.items():
        path = DOCS / f"benchmark-distribution-{name}.svg"
        path.write_text(distribution_chart(rows, theme), encoding="utf-8")
        print("written:", path)
        path = DOCS / f"benchmark-techniques-{name}.svg"
        path.write_text(usage_chart(theme, usage, solved), encoding="utf-8")
        print("written:", path)


if __name__ == "__main__":
    main()
