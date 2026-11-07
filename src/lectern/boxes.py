"""Boxes and marks: definition boxes, terminal output, outlines, crossing out."""

from manim import DL, DOWN, DR, LEFT, UL, UR, Line, Rectangle, SurroundingRectangle, VGroup

from lectern.text import mono, split_lines, styled
from lectern.theme import T

__all__ = ["definition_box", "compact_box", "term", "red_x", "surround", "lit_box"]


def definition_box(label, lines, font_size=28, width=None, pad=0.35, max_w=12.0):
    """`definition box: <label>` in a script: a rectangle with `label` set into its
    top border and `lines` (prose with markup) inside, wrapped to fit `max_w`."""
    wrapped = []
    for l in lines:
        wrapped.extend(split_lines(l, font_size, max_w - 2 * pad))
    content = VGroup(*[styled(l, font_size=font_size) for l in wrapped])
    content.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    label_mob = styled(f"**{label}**", font_size=font_size + 2)
    box_width = width or max(content.width, label_mob.width + 0.5) + 2 * pad
    box = Rectangle(width=box_width, height=content.height + 2 * pad + 0.2, color=T.text)
    content.move_to(box.get_center() + DOWN * 0.1)
    # A background-colored patch hides the border behind the label.
    label_bg = Rectangle(width=label_mob.width + 0.3, height=label_mob.height + 0.2,
                         fill_color=T.background, fill_opacity=1, stroke_width=0)
    label_group = VGroup(label_bg, label_mob).move_to(box.get_top())
    return VGroup(box, content, label_group)


def compact_box(label, lines, font_size=24, max_w=6.0):
    """A smaller definition box, for a pane."""
    return definition_box(label, lines, font_size=font_size, pad=0.25, max_w=max_w)


def term(text, font_size=22, width=None):
    """A terminal window showing lines of output."""
    t = VGroup(*[mono(l, font_size=font_size) for l in text.split("\n")]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    r = SurroundingRectangle(t, color=T.muted, buff=0.18, fill_color=T.panel, fill_opacity=1, corner_radius=0.05)
    return VGroup(r, t)


def red_x(mob):
    """Two lines crossing out `mob`, in the theme's `bad` color."""
    a, b = mob.get_corner(UL), mob.get_corner(DR)
    c, d = mob.get_corner(UR), mob.get_corner(DL)
    return VGroup(Line(a, b, color=T.bad, stroke_width=6), Line(c, d, color=T.bad, stroke_width=6))


def surround(mob, color=None, buff=0.06):
    return SurroundingRectangle(mob, color=color or T.focus, buff=buff)


def lit_box(b, color=None, opacity=0.35):
    """Animation: fill and outline a box (any VGroup whose first member is its
    shape) in `color`. STYLE.md: highlighting a cell means changing its background."""
    color = color or T.focus
    return b[0].animate.set_fill(color, opacity=opacity).set_stroke(color)
