"""Tables, from the markdown table syntax in SCRIPT_CONVENTIONS.md.

Two looks. `table()` draws only a rule under the header:

    t = table([["op", "meaning"],
               ["`+`", "add"],
               ["`*`", "multiply"]])
    self.page("Operators", H(t), self.rows(t))   # reveal one row per pause

`grid_table()` draws every cell's border (a manim MobjectTable):

    t = grid_table(rows)
    self.reveal_grid_table(t)                    # grid and header, then a row per pause
"""

from manim import Line, MobjectTable, Rectangle, VGroup

from lectern.text import styled
from lectern.theme import T

__all__ = ["table", "grid_table"]


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


def grid_table(rows, font_size=26, header=True, h_buff=0.6, v_buff=0.28, cell=None, line_config=None):
    """A table with every cell's border drawn. `rows` as in `table()`; the header row
    is bold (except math, which can't take prose bold). `cell(text, r, c)` may
    return a mobject to use for that cell instead of styled text (or None for
    the default). Returns a manim MobjectTable: `t.get_rows()`, `t.get_cell((r, c))`, ...."""
    mobs = []
    for r, row in enumerate(rows):
        out = []
        for c, text in enumerate(row):
            m = cell(text, r, c) if cell is not None else None
            if m is None:
                s = str(text)
                bold = header and r == 0 and s.strip() and "$" not in s
                m = styled(f"**{s}**" if bold else s, font_size=font_size)
            out.append(m)
        mobs.append(out)
    lines = {"stroke_width": 2, "color": T.text}
    lines.update(line_config or {})
    return MobjectTable(mobs, h_buff=h_buff, v_buff=v_buff, include_outer_lines=True, line_config=lines)
