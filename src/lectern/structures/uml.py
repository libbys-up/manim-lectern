"""UML class-diagram visuals for Manim: `UMLClass` (the three-compartment class
box) and `UMLLink` (an association or composition line between two boxes).

`UMLClass` rows are monospace `Text`, one mobject per attribute/operation, looked
up by their text (`row("- balance : double")`) and sliced by substring
(`part(row_text, ": double")`) so stage directions can point at single rows or
pieces of them. Each row carries an invisible `|` strut as its first glyph so
every row is the same height and rows sit on a common baseline, whatever
letters they contain.

The box's top-left corner is its anchor: `remove_row` shrinks the box upward
toward it (rows below the removed one slide up) rather than re-centering.

`UMLLink` endpoints are computed once, at construction, from the boxes' current
frames (or from explicit `start`/`end` points) -- build links after the boxes
are in their final places.

Mutating methods return Animations rather than playing them.
"""

from manim import *
import numpy as np
from lectern.theme import T
from lectern.alt import AltText, count, describe_tree, words


UML_FONT = "Monospace"


class UMLClass(AltText, VGroup):
    def __init__(self, name, attributes=(), operations=(), font_size=20, color=None,
                 pad_x=0.2, pad_y=0.12, row_gap=0.08, min_width=0.0, empty_height=0.3):
        color = T.text if color is None else color
        super().__init__()
        self.name = name
        self.attributes, self.operations = list(attributes), list(operations)
        self.font_size = font_size
        self.color = color
        self.pad_x = pad_x
        self.pad_y = pad_y
        self.row_gap = row_gap
        self.min_width = min_width
        self.empty_height = empty_height

        self.name_row = self._make_row(name, weight=BOLD)
        self.attr_rows = [self._make_row(a) for a in attributes]
        self.op_rows = [self._make_row(o) for o in operations]
        self.line_height = self.name_row.height

        self.box = None
        layout = self._layout(self.attr_rows, self.op_rows)
        self.box, self.dividers = self._frame(layout)
        for row, (x, y) in layout["rows"].items():
            self._place(row, x, y)
        self.add(self.box, self.dividers, self.name_row, *self.attr_rows, *self.op_rows)
        self.center()

    def describe(self):
        out = [f"UML class {self.name}."]
        if self.attributes:
            out.append(f"Attributes: {'; '.join(self.attributes)}.")
        if self.operations:
            out.append(f"Operations: {'; '.join(self.operations)}.")
        return " ".join(out)

    # ---------- construction ----------

    def _make_row(self, text, weight=NORMAL):
        t = Text("|" + text, font=UML_FONT, font_size=self.font_size, color=self.color, weight=weight)
        strut = t[0]
        strut.set_opacity(0)
        if len(t) > 1:
            strut.set_x(t[1].get_left()[0] + strut.width / 2)
        t.text = text
        return t

    def _layout(self, attr_rows, op_rows):
        """Logical layout from the box's current top-left corner: compartment boundaries and
        the (left x, top y) of every row (the name row's x is its center)."""
        widths = [self.name_row.width] + [r.width for r in attr_rows + op_rows]
        width = max(self.min_width, max(widths) + 2 * self.pad_x)
        top_left = self.box.get_corner(UL) if self.box is not None else ORIGIN
        x0, y = top_left[0], top_left[1]
        slot = self.line_height + self.row_gap
        rows = {}

        rows[self.name_row] = (x0 + width / 2, y - self.pad_y)
        y_div1 = y - self.line_height - 2 * self.pad_y

        def section(section_rows, y_top):
            if not section_rows:
                return y_top - self.empty_height
            for i, row in enumerate(section_rows):
                rows[row] = (x0 + self.pad_x, y_top - self.pad_y - i * slot)
            return y_top - 2 * self.pad_y - len(section_rows) * slot + self.row_gap

        y_div2 = section(attr_rows, y_div1)
        y_bottom = section(op_rows, y_div2)
        return {"width": width, "x0": x0, "top": y, "div1": y_div1, "div2": y_div2,
                "bottom": y_bottom, "rows": rows}

    def _frame(self, layout):
        x0, w = layout["x0"], layout["width"]
        top, bottom = layout["top"], layout["bottom"]
        box = Rectangle(width=w, height=top - bottom, color=self.color, stroke_width=2)
        box.move_to([x0 + w / 2, (top + bottom) / 2, 0])
        dividers = VGroup(*[
            Line([x0, layout[k], 0], [x0 + w, layout[k], 0], color=self.color, stroke_width=2)
            for k in ("div1", "div2")
        ])
        return box, dividers

    def _target_shift(self, row, x, y):
        if row is self.name_row:
            return np.array([x - row.get_center()[0], y - row.get_top()[1], 0])
        return np.array([x - row.get_left()[0], y - row.get_top()[1], 0])

    def _place(self, row, x, y):
        row.shift(self._target_shift(row, x, y))

    # ---------- lookup ----------

    @property
    def rows(self):
        return [self.name_row] + self.attr_rows + self.op_rows

    def row(self, text):
        """The row whose text is `text`, or else the one row whose text starts with it."""
        exact = [r for r in self.rows if r.text == text]
        if exact:
            return exact[0]
        prefix = [r for r in self.rows if r.text.startswith(text)]
        if len(prefix) != 1:
            raise ValueError(f"{self.name}: no unique row matching {text!r}")
        return prefix[0]

    def part(self, row_text, substring, occurrence=0):
        """The glyphs of `substring` within a row (spaces aren't glyphs, so
        indices count non-space characters; glyph 0 is the invisible strut)."""
        row = self.row(row_text)
        idx = -1
        for _ in range(occurrence + 1):
            idx = row.text.index(substring, idx + 1)
        start = 1 + sum(1 for c in row.text[:idx] if not c.isspace())
        length = sum(1 for c in substring if not c.isspace())
        return VGroup(*row[start:start + length])

    def visible(self, row):
        """A row without its strut -- for highlights/transforms that should hug the text."""
        row = self.row(row) if isinstance(row, str) else row
        return VGroup(*row[1:])

    def compartment(self, which):
        """Rectangle covering compartment "name" / "attributes" / "operations"."""
        box, (d1, d2) = self.box, self.dividers
        top, bottom = {
            "name": (box.get_top()[1], d1.get_y()),
            "attributes": (d1.get_y(), d2.get_y()),
            "operations": (d2.get_y(), box.get_bottom()[1]),
        }[which]
        rect = Rectangle(width=box.width, height=top - bottom)
        rect.move_to([box.get_x(), (top + bottom) / 2, 0])
        return rect

    # ---------- parts for revealing ----------

    def frame_with_name(self):
        """The box, dividers and name -- everything but the attribute/operation rows."""
        return VGroup(self.box, self.dividers, self.name_row)

    # ---------- mutation ----------

    def strike(self, row_text, color=None) -> Animation:
        """Draw a line through a row; the line is kept on the row and goes away with it."""
        color = T.bad if color is None else color
        row = self.row(row_text)
        body = self.visible(row)
        row.strike_line = Line(body.get_left() + LEFT * 0.05, body.get_right() + RIGHT * 0.05,
                               color=color, stroke_width=4)
        self.add(row.strike_line)
        return Create(row.strike_line)

    def remove_rows(self, *row_texts):
        """Fade out the given rows and shrink the box around the rest, top-left fixed."""
        doomed = [self.row(t) for t in row_texts]
        anims = []
        for row in doomed:
            anims.append(FadeOut(row))
            if hasattr(row, "strike_line"):
                anims.append(FadeOut(row.strike_line))
                self.remove(row.strike_line)
            self.remove(row)
        self.attr_rows = [r for r in self.attr_rows if r not in doomed]
        self.op_rows = [r for r in self.op_rows if r not in doomed]

        layout = self._layout(self.attr_rows, self.op_rows)
        new_box, new_dividers = self._frame(layout)
        anims += [Transform(self.box, new_box), Transform(self.dividers, new_dividers)]
        for row, (x, y) in layout["rows"].items():
            delta = self._target_shift(row, x, y)
            if np.linalg.norm(delta) > 1e-6:
                anims.append(row.animate.shift(delta))
        return anims


class UMLLink(AltText, VGroup):
    """A line from `owner` to `other`.

    kind="composition": filled diamond at the owner end.
    kind="aggregation": hollow diamond at the owner end.
    kind="association": plain line; open arrowhead at the `other` end if `navigable`.

    `owner_mult` / `other_mult` are multiplicity labels at each end and `role` is
    the role (field) name at the `other` end. `label_side` (+1 / -1) picks which
    side of the line the multiplicities go on; the role goes on the other side.
    `offset` slides the whole line sideways (perpendicular to its direction),
    e.g. for two parallel links between the same boxes.
    """

    def __init__(self, owner, other, kind="composition", owner_mult=None, other_mult=None,
                 role=None, start=None, end=None, offset=0.0, navigable=True, label_side=1,
                 font_size=18, color=None, diamond_length=0.38, diamond_width=0.24):
        color = T.text if color is None else color
        super().__init__()
        self.kind = kind
        self.color = color
        # Names, not the boxes: a reference to a box would be deep-copied by .animate.
        self.owner_name, self.other_name = getattr(owner, "name", None), getattr(other, "name", None)
        self.owner_mult, self.other_mult, self.role = owner_mult, other_mult, role
        owner_box = getattr(owner, "box", owner)
        other_box = getattr(other, "box", other)

        c1, c2 = owner_box.get_center(), other_box.get_center()
        direction = c2 - c1
        u = direction / np.linalg.norm(direction)
        n = np.array([-u[1], u[0], 0])
        if start is None:
            start = self._clip_to_box(c1 + n * offset, owner_box, u)
        if end is None:
            end = self._clip_to_box(c2 + n * offset, other_box, -u)
        start, end = np.array(start, dtype=float), np.array(end, dtype=float)
        u = (end - start) / np.linalg.norm(end - start)
        n = np.array([-u[1], u[0], 0])
        self.start, self.end, self.u, self.n = start, end, u, n

        line_start = start
        if kind in ("composition", "aggregation"):
            tip, back = start, start + u * diamond_length
            mid = start + u * diamond_length / 2
            self.head = Polygon(tip, mid + n * diamond_width / 2, back, mid - n * diamond_width / 2,
                                color=color, stroke_width=2)
            if kind == "composition":
                self.head.set_fill(color, opacity=1)
            else:
                self.head.set_fill(T.background, opacity=1)
            line_start = back
        elif kind == "association" and navigable:
            size = 0.22
            self.head = VGroup(*[
                Line(end, end - u * size * np.cos(PI / 6) + side * n * size * np.sin(PI / 6),
                     color=color, stroke_width=2)
                for side in (1, -1)
            ])
        else:
            self.head = VGroup()

        self.line = Line(line_start, end, color=color, stroke_width=2)

        head_len = diamond_length if kind in ("composition", "aggregation") else 0.0
        self.owner_label = self._end_label(owner_mult, start, u, owner_box, label_side, font_size, head_len)
        self.other_label = self._end_label(other_mult, end, -u, other_box, label_side, font_size)
        self.role_label = self._end_label(role, end, -u, other_box, -label_side, font_size)
        self.labels = VGroup(*[m for m in (self.owner_label, self.other_label, self.role_label) if m is not None])

        self.add(self.line, self.head, self.labels)

    def describe(self):
        a, b = self.owner_name or "a class", self.other_name or "a class"
        out = f"A UML {self.kind} from {a} to {b}"
        mults = [f"{m} at {n}" for m, n in ((self.owner_mult, a), (self.other_mult, b)) if m]
        if mults:
            out += f", multiplicity {words(mults)}"
        if self.role:
            out += f", role {self.role}"
        return out + "."

    @staticmethod
    def _clip_to_box(point, box, u):
        """Where the ray from `point` (inside `box`) along `u` leaves the box."""
        c = box.get_center()
        hw, hh = box.width / 2, box.height / 2
        ts = []
        if abs(u[0]) > 1e-9:
            ts += [((c[0] + s * hw) - point[0]) / u[0] for s in (1, -1)]
        if abs(u[1]) > 1e-9:
            ts += [((c[1] + s * hh) - point[1]) / u[1] for s in (1, -1)]
        t = min(t for t in ts if t > 0)
        return point + u * t

    def _end_label(self, text, point, inward, box, side, font_size, clearance=0.0):
        """A label just off the line near `point`, on `side` of it, clear of `box`.
        `inward` points from that end along the line, away from its box."""
        if not text:
            return None
        label = Text(text, font=UML_FONT, font_size=font_size, color=self.color)
        hw, hh = label.width / 2, label.height / 2
        n = np.array([-self.u[1], self.u[0], 0]) * side
        along = abs(inward[0]) * hw + abs(inward[1]) * hh + 0.12 + clearance
        across = abs(n[0]) * hw + abs(n[1]) * hh + 0.22
        label.move_to(point + inward * along + n * across)
        return label

    def create(self) -> Animation:
        parts = [Create(self.line)]
        if len(self.head.submobjects) or self.head.has_points():
            parts.append(FadeIn(self.head))
        if len(self.labels):
            parts.append(FadeIn(self.labels))
        return LaggedStart(*parts, lag_ratio=0.6)

    def recolor(self, color):
        """Animations that recolor the line and its head (not the labels)."""
        anims = [self.line.animate.set_color(color)]
        if self.kind == "composition":
            anims.append(self.head.animate.set_color(color))
        elif self.kind == "aggregation":
            anims.append(self.head.animate.set_stroke(color))
        elif len(self.head.submobjects):
            anims.append(self.head.animate.set_color(color))
        return anims


__all__ = ["UMLClass", "UMLLink", "UML_FONT"]
