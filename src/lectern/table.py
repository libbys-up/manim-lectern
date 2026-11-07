"""Tables, from the markdown table syntax in SCRIPT_CONVENTIONS.md.

    t = table([["op", "meaning"],
               ["`+`", "add"],
               ["`*`", "multiply"]])
    self.page("Operators", H(t), self.rows(t))   # reveal one row per pause
"""

from manim import Line, Rectangle, VGroup

from lectern.text import styled
from lectern.theme import T

__all__ = ["table"]


def table(rows, font_size=24, header=True, gap_x=0.5, gap_y=0.18):
    """`rows` is a list of rows, each a list of cell strings (with markup). The first
    row is the header: bold, with a rule under it. `t.rows_[i]` is row i, a VGroup."""
    built = []
    for r, row in enumerate(rows):
        cells = []
        for cell in row:
            s = str(cell)
            if header and r == 0 and s and "$" not in s:  # math can't take prose bold
                s = f"**{s}**"
            m = styled(s, font_size=font_size) if s else Rectangle(width=0.01, height=0.25, stroke_opacity=0)
            cells.append(m)
        built.append(cells)
    ncol = max(len(r) for r in built)
    widths = [max(r[j].width for r in built if j < len(r)) for j in range(ncol)]
    heights = [max(max(c.height for c in r), 0.28) for r in built]
    group = VGroup()
    group.rows_ = []
    y = 0.0
    total = sum(widths) + gap_x * (ncol - 1)
    for r, cells in enumerate(built):
        x = 0.0
        row = VGroup()
        for j, c in enumerate(cells):
            c.move_to([x + c.width / 2, y - heights[r] / 2, 0])
            x += widths[j] + gap_x
            row.add(c)
        if header and r == 0:
            row.add(Line([-0.1, y - heights[r] - gap_y / 2, 0], [total + 0.1, y - heights[r] - gap_y / 2, 0],
                         stroke_width=2, color=T.muted))
        group.add(row)
        group.rows_.append(row)
        y -= heights[r] + gap_y
    return group
