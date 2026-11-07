"""`Row`: a row of labeled cells, sized to their contents: the characters of an input,
a stream of tokens, a short array of values.

    r = chars("x = 42;")           # one cell per character
    r = tokens("ID:x = NUM:42 ;")  # one cell per token; "kind:value" stacks the kind above
    arrow = r.cursor(0)            # a pointer above cell 0
    self.play(r.cursor_to(arrow, 3), r.fill(3))

For an array with indices, push/pop, and swaps, see Array in lectern.structures.array.
"""

from manim import DOWN, UP, Arrow, Brace, DashedVMobject, Rectangle, SurroundingRectangle, VGroup, ORIGIN

from lectern.text import mono
from lectern.theme import T

__all__ = ["Row", "chars", "tokens"]


class Row(VGroup):

    def __init__(self, items, cell_h=0.6, font_size=26, min_w=0.55, gap=0.0):
        super().__init__()
        self.boxes, self.vals = VGroup(), VGroup()
        x = 0.0
        for it in items:
            kind, _, value = str(it).partition(":")
            if value:
                t = VGroup(mono(kind, font_size=font_size - 10, color=T.subtle),
                           mono(value, font_size=font_size - 2)).arrange(DOWN, buff=0.04)
            else:
                t = mono(kind, font_size=font_size)
                if kind == " ":  # a space cell is empty, but keeps its width
                    t.set_opacity(0)
            w = max(min_w, t.width + 0.22)
            b = Rectangle(width=w, height=cell_h, stroke_width=2, color=T.text).move_to([x + w / 2, 0, 0])
            t.move_to(b)
            x += w + gap
            self.boxes.add(b)
            self.vals.add(t)
        self.add(self.boxes, self.vals)
        self.move_to(ORIGIN)

    def cell(self, i):
        return VGroup(self.boxes[i], self.vals[i])

    def fill(self, i, color=None, opacity=0.4):
        """Animation: color cell i's background."""
        return self.boxes[i].animate.set_fill(color or T.focus, opacity=opacity)

    def clear(self, i):
        return self.boxes[i].animate.set_fill(opacity=0)

    def span(self, i, j):
        """Cells i through j, inclusive."""
        return VGroup(*self.boxes[i:j + 1])

    def bracket(self, i, j, label=None, color=None, direction=DOWN, font_size=20):
        """A brace under (or over) cells i..j, with an optional label."""
        color = color or T.text
        br = Brace(self.span(i, j), direction, buff=0.06, color=color)
        if label is None:
            return VGroup(br)
        return VGroup(br, mono(label, font_size=font_size, color=color).next_to(br, direction, buff=0.06))

    def cursor(self, i, color=None):
        """An arrow pointing down at cell i (not added)."""
        tip = self.boxes[i].get_top() + UP * 0.05
        return Arrow(tip + UP * 0.55, tip, buff=0, color=color or T.current, stroke_width=4, tip_length=0.18,
                     max_tip_length_to_length_ratio=0.4)

    def cursor_to(self, arrow, i):
        """Animation: slide a cursor to cell i."""
        return arrow.animate.set_x(self.boxes[i].get_center()[0])

    def peek(self, i, color=None):
        """A dashed outline around cell i: looking at it without consuming it."""
        return DashedVMobject(SurroundingRectangle(self.boxes[i], color=color or T.focus, buff=0.04), num_dashes=16)


def chars(text, **kw):
    return Row(list(text), **kw)


def tokens(text, **kw):
    return Row(text.split(), **kw)
