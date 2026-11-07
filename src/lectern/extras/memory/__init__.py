"""Memory diagrams: columns of memory cells, the run-time stack, and pointers into them.

    from lectern.extras.memory import Mem, StackView

    m = Mem([("8", "x"), ("tag", None), ("0x1000", "p")])    # value, label on the left
    self.play(m.put(0, "9", src=some_register_value))         # the value moves in

    s = StackView(top=(3, 2.5), addrs=True)
    self.add(*s.start_mobs())
    self.go(s.push("42", name="x"))

High addresses are at the top of the screen and the stack grows down (conventions:
CONVENTIONS.md in this folder). Every method that changes a value takes `src=`:
something on screen whose copy moves into the cell (see lectern.anim.arrive).

Cells whose value is in `dim_values` (by default "tag" and "GC tag", for GC headers)
are drawn in the theme's muted color.
"""

import numpy as np
from manim import DOWN, LEFT, RIGHT, Arrow, FadeIn, FadeOut, Line, Rectangle, Transform, VGroup

from lectern.anim import arrive
from lectern.text import mono
from lectern.theme import T

__all__ = ["Mem", "Pointer", "StackView"]


class Mem(VGroup):
    """A column of memory cells. `cells`: "value" or ("value", "label"). The label
    goes to the left of the cell."""

    dim_values = ("tag", "GC tag", "GC Tag")

    def __init__(self, cells, width=3.0, height=0.5, font_size=22, label_size=20):
        super().__init__()
        self.boxes, self.vals, self.labs = VGroup(), VGroup(), VGroup()
        self.h = height
        for i, c in enumerate(cells):
            val, lab = c if isinstance(c, tuple) else (c, None)
            dim = str(val) in self.dim_values
            box = Rectangle(width=width, height=height, stroke_width=2, color=T.muted if dim else T.text)
            box.move_to([0, -i * height, 0])
            t = mono(val, font_size=font_size - 3 if dim else font_size, color=T.muted if dim else T.text)
            if t.width > width - 0.15:
                t.scale_to_fit_width(width - 0.15)
            t.move_to(box)
            self.boxes.add(box)
            self.vals.add(t)
            # Every cell gets a label mobject, invisible if it has no label, so
            # relabel() always has something to transform.
            lb = mono(lab if lab else " ", font_size=label_size, color=T.label)
            lb.next_to(box, LEFT, buff=0.15)
            if not lab:
                lb.set_opacity(0)
            self.labs.add(lb)
        self.add(self.boxes, self.vals, self.labs)

    def cell(self, i):
        return VGroup(self.boxes[i], self.vals[i])

    def row(self, i):
        return VGroup(self.boxes[i], self.vals[i], self.labs[i])

    def fill(self, i, color=None, opacity=0.4):
        return self.boxes[i].animate.set_fill(color or T.focus, opacity=opacity)

    def clear(self, i):
        return self.boxes[i].animate.set_fill(opacity=0)

    def put(self, i, text, color=None, src=None):
        """Animation: cell i's value becomes `text`, carried from `src` if given."""
        new = mono(text, font_size=22, color=color or T.text)
        if new.width > self.boxes[i].width - 0.15:
            new.scale_to_fit_width(self.boxes[i].width - 0.15)
        new.move_to(self.boxes[i])
        return arrive(self.vals[i], new, src)

    def relabel(self, i, text):
        new = mono(text, font_size=20, color=T.label).move_to(self.labs[i]).align_to(self.labs[i], RIGHT)
        new.next_to(self.boxes[i], LEFT, buff=0.15)
        return Transform(self.labs[i], new)

    def pointer(self, i, name="$sp", color=None, side=RIGHT):
        return Pointer(self.boxes[i], name, color, side)


class Pointer(VGroup):
    """A named arrow pointing at a cell from the side."""

    def __init__(self, target, name="$sp", color=None, side=RIGHT, length=0.7):
        super().__init__()
        color = color or T.current
        self.side = side
        tip = target.get_edge_center(side) + side * 0.05
        self.arrow = Arrow(tip + side * length, tip, buff=0, color=color, stroke_width=4, tip_length=0.18,
                           max_tip_length_to_length_ratio=0.4)
        self.name_ = mono(name, font_size=22, color=color).next_to(self.arrow, side, buff=0.08)
        self.add(self.arrow, self.name_)

    def to(self, target):
        """Animation: move the pointer to another cell."""
        tip = target.get_edge_center(self.side) + self.side * 0.05
        return self.animate.shift(tip - self.arrow.get_end())


class StackView:
    """A run-time stack that grows down the screen from `top`, with a $sp pointer.

    Not a mobject: cells are created as values are pushed and removed as they're
    popped. Each method returns a list of animations; pass them to `self.go(...)`.
    Start with `self.add(*stack.start_mobs())`.

    `addrs=True` labels cells with addresses counting down from `start`, 4 bytes each;
    otherwise each cell is labeled with the `name` it was pushed with."""

    dim_values = ("tag", "5")

    def __init__(self, top, width=2.6, height=0.42, addrs=False, start=0x8000, sp=True, font_size=22):
        self.top = np.array(list(top) + [0] * (3 - len(top)), dtype=float)  # (x, y) or (x, y, z)
        self.w, self.h = width, height
        self.font_size = font_size
        self.cells = []  # dicts: box, val, lab, name
        self.addrs = addrs
        self.start = start
        self.base = Line(self.top + LEFT * width / 2, self.top + RIGHT * width / 2, stroke_width=4, color=T.text)
        self.sp = None
        if sp:
            self.sp = Pointer(self.base, "$sp")
            self.sp.shift(self.top + RIGHT * width / 2 + RIGHT * 0.05 - self.sp.arrow.get_end())

    def start_mobs(self):
        """What to add before the first push: the base line and $sp."""
        out = [self.base]
        if self.sp:
            out.append(self.sp)
        return out

    def pos(self, i):
        """Center of cell i (0 is the oldest, at the top)."""
        return self.top + DOWN * (i + 0.5) * self.h

    def _sp_to(self, i):
        if not self.sp:
            return []
        y = self.pos(i) if i >= 0 else self.top
        tip = np.array([self.top[0] + self.w / 2 + 0.05, y[1], 0])
        return [self.sp.animate.shift(tip - self.sp.arrow.get_end())]

    def label_for(self, i, name):
        text = hex(self.start - 4 * i) if self.addrs else (name or " ")
        lab = mono(text, font_size=18, color=T.label)
        lab.next_to(self.pos(i) + LEFT * self.w / 2, LEFT, buff=0.12)
        if not name and not self.addrs:
            lab.set_opacity(0)
        return lab

    def make(self, text, name=None, color=None):
        """Create cell mobjects for a push, without animating."""
        i = len(self.cells)
        dim = str(text) in self.dim_values
        box = Rectangle(width=self.w, height=self.h, stroke_width=2, color=T.muted if dim else T.text).move_to(self.pos(i))
        val = mono(text, font_size=self.font_size - (3 if dim else 0), color=T.muted if dim else (color or T.text))
        if val.width > self.w - 0.1:
            val.scale_to_fit_width(self.w - 0.1)
        val.move_to(box)
        lab = self.label_for(i, name)
        cell = dict(box=box, val=val, lab=lab, name=name)
        self.cells.append(cell)
        return cell

    def push(self, text, name=None, color=None, src=None):
        """Push a value. `src`: where it comes from; its copy moves into the new cell."""
        cell = self.make(text, name, color)
        if src is None:
            return [FadeIn(VGroup(cell["box"], cell["val"], cell["lab"]), shift=DOWN * 0.15)] + self._sp_to(len(self.cells) - 1)
        # An empty placeholder appears with the cell; arrive() turns it into the value.
        val = cell["val"]
        cell["val"] = mono(" ", font_size=self.font_size).move_to(cell["box"])
        return ([FadeIn(VGroup(cell["box"], cell["val"], cell["lab"]), shift=DOWN * 0.15), arrive(cell["val"], val, src)]
                + self._sp_to(len(self.cells) - 1))

    def push_int(self, text, name=None):
        """Push a boxed integer: a GC tag, then the value."""
        return self.push("tag") + self.push(text, name)

    def pop(self, n=1):
        anims = []
        for _ in range(n):
            cell = self.cells.pop()
            anims.append(FadeOut(VGroup(cell["box"], cell["val"], cell["lab"])))
        return anims + self._sp_to(len(self.cells) - 1)

    def cell(self, i):
        return self.cells[i]["box"]

    def top_cell(self):
        return self.cells[-1]["box"]

    def val(self, i):
        return self.cells[i]["val"]

    def set_val(self, i, text, color=None, src=None):
        """Animation: cell i's value becomes `text`, carried from `src` if given."""
        new = mono(text, font_size=self.font_size, color=color or T.text).move_to(self.cells[i]["box"])
        return arrive(self.cells[i]["val"], new, src)

    def fill(self, i, color=None, opacity=0.4):
        return self.cells[i]["box"].animate.set_fill(color or T.focus, opacity=opacity)

    def clear(self, i):
        return self.cells[i]["box"].animate.set_fill(opacity=0)

    def offsets(self, name_for=None):
        """Relabel every named cell with its offset from $sp, keeping its name."""
        anims = []
        for i, c in enumerate(self.cells):
            if not c["name"] or c["name"] == "tag":
                continue
            off = 4 * (len(self.cells) - 1 - i)
            text = f"{c['name']} @ {off}($sp)" if off else f"{c['name']} @ ($sp)"
            new = mono(text, font_size=18, color=T.label)
            new.next_to(self.pos(i) + LEFT * self.w / 2, LEFT, buff=0.12)
            anims.append(Transform(c["lab"], new))
        return anims

    def everything(self):
        out = VGroup(self.base)
        for c in self.cells:
            out.add(c["box"], c["val"], c["lab"])
        return out
