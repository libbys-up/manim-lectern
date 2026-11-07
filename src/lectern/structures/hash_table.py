"""Bucket-chaining hash table visual.

A horizontal row of bucket cells (index labels above them), each with a
vertical linked list hanging below it:

      0     1     2
    [ X ] [ • ] [ X ]
            |
            v
          [ 21 |•]
            |
            v
          [ 1  |X]

A bucket cell shows an X when its list is empty and a dot (with an arrow down
to the first node) otherwise. Each node is one box per field (one field for a
set, `key | value` for a map) plus a pointer square that holds an X on the last
node of the chain.

Node positions and arrows are computed analytically from (bucket, depth), not
read off live mobjects, so a chain can be re-pointed while its nodes are still
mid-`.animate`. Nodes keep no references to each other -- the table's
`chains` lists are the only bookkeeping -- so `.animate` on a node never has to
deep-copy a whole chain.
"""

from typing import List, Optional, Sequence

from manim import *
from lectern.theme import T


class ChainNode(VGroup):
    """[ field | field ... | ptr ] -- the ptr square holds an X when it's the last node."""

    def __init__(self, fields: Sequence, field_widths: Sequence[float], height=0.55, font_size=22):
        super().__init__()
        self.values = [str(f) for f in fields]
        self.height_ = height
        self.font_size = font_size

        self.boxes = VGroup()
        self.labels = VGroup()
        x = 0.0
        for value, w in zip(self.values, field_widths):
            box = Rectangle(width=w, height=height, stroke_color=T.text, stroke_width=2)
            box.move_to([x + w / 2, 0, 0])
            label = Text(value, font_size=font_size).move_to(box)
            self.boxes.add(box)
            self.labels.add(label)
            x += w
        self.ptr = Square(side_length=height * 0.7, stroke_color=T.text, stroke_width=2)
        self.ptr.stretch_to_fit_height(height).move_to([x + height * 0.35, 0, 0])
        self.dot = Dot(radius=height / 9, color=T.text).move_to(self.ptr)
        self.cross = self._cross()
        self.add(self.boxes, self.ptr, self.labels, self.dot, self.cross)
        self.center()

    def _cross(self):
        s = self.ptr
        return VGroup(
            Line(s.get_corner(UL), s.get_corner(DR), color=T.text, stroke_width=2),
            Line(s.get_corner(DL), s.get_corner(UR), color=T.text, stroke_width=2),
        )

    @property
    def value(self):
        return self.values[0]

    def show_null(self, is_null: bool):
        """Not animated: X in the pointer square for the last node, dot otherwise."""
        self.cross.set_opacity(1 if is_null else 0)
        self.dot.set_opacity(0 if is_null else 1)

    def highlight(self, color=None, opacity=0.4) -> Animation:
        color = T.focus if color is None else color
        return self.boxes.animate.set_fill(color, opacity=opacity)

    def unhighlight(self) -> Animation:
        return self.boxes.animate.set_fill(opacity=0)

    def highlight_field(self, field, color=None, opacity=0.4) -> Animation:
        color = T.focus if color is None else color
        return self.boxes[field].animate.set_fill(color, opacity=opacity)

    def set_field(self, field, new_value) -> Animation:
        old = self.labels[field]
        new = Text(str(new_value), font_size=self.font_size).move_to(self.boxes[field])
        self.values[field] = str(new_value)
        self.labels.submobjects[field] = new
        return ReplacementTransform(old, new)


class ChainedHashTable(VGroup):
    """Row of `size` bucket cells, each with a vertical chain of `ChainNode`s.

    `field_widths` gives one width per node field (e.g. `[0.8]` for a set,
    `[1.2, 0.6]` for key|value pairs). `slot_width` is the horizontal spacing
    between bucket centers; it defaults to just wider than a node.
    """

    def __init__(self, size, field_widths=(0.8,), cell_size=0.6, node_height=0.5, slot_width=None,
                 node_gap=0.35, start_point=ORIGIN, font_size=22, index_font_size=18, show_indices=True):
        super().__init__()
        self.size = size
        self.field_widths = list(field_widths)
        self.cell_size = cell_size
        self.node_height = node_height
        self.node_width = sum(self.field_widths) + node_height * 0.7
        self.slot_width = slot_width or max(cell_size, self.node_width) + 0.15
        self.node_gap = node_gap
        self.start_point = np.array(start_point, dtype=float)
        self.font_size = font_size

        self.cells = VGroup()
        self.indices = VGroup()
        self.cell_crosses: List[VGroup] = []
        self.cell_dots: List[Dot] = []
        for b in range(size):
            cell = Square(side_length=cell_size, stroke_color=T.text, stroke_width=2).move_to(self.cell_center(b))
            cross = VGroup(
                Line(cell.get_corner(UL), cell.get_corner(DR), color=T.text, stroke_width=2),
                Line(cell.get_corner(DL), cell.get_corner(UR), color=T.text, stroke_width=2),
            ).scale(0.6)
            dot = Dot(radius=cell_size / 10, color=T.text).move_to(cell).set_opacity(0)
            idx = Text(str(b), font_size=index_font_size).next_to(cell, UP, buff=0.12)
            if not show_indices:
                idx.set_opacity(0)
            self.cells.add(cell)
            self.indices.add(idx)
            self.cell_crosses.append(cross)
            self.cell_dots.append(dot)
            self.add(cell, cross, dot, idx)

        self.chains: List[List[ChainNode]] = [[] for _ in range(size)]
        # arrows[b][k] is the arrow *into* node k of bucket b (k=0: from the bucket cell).
        self.arrows: List[List[Arrow]] = [[] for _ in range(size)]

    @classmethod
    def from_lists(cls, lists, **kwargs):
        """`lists[b]` is bucket b's chain, front first. Values may be tuples of fields."""
        table = cls(len(lists), **kwargs)
        for b, chain in enumerate(lists):
            for k, fields in enumerate(chain):
                node = table._make_node(fields).move_to(table.node_center(b, k))
                table.chains[b].append(node)
                table.add(node)
            table._rebuild_static(b)
        return table

    def place(self, point):
        """Not animated: move the table so its row of bucket cells is centered
        on `point`, keeping the analytic layout (`start_point`) in step."""
        delta = np.array(point, dtype=float) - self.cells.get_center()
        self.shift(delta)
        self.start_point = self.start_point + delta
        return self

    # ---------- geometry ----------

    def cell_center(self, b):
        return self.start_point + RIGHT * self.slot_width * b

    def node_center(self, b, k):
        top = self.cell_center(b)[1] - self.cell_size / 2 - self.node_gap
        y = top - self.node_height / 2 - k * (self.node_height + self.node_gap)
        return np.array([self.cell_center(b)[0], y, 0])

    def _ptr_x(self, b):
        """x of a node's pointer-square center in bucket b."""
        return self.cell_center(b)[0] + self.node_width / 2 - self.node_height * 0.35

    def _arrow_start(self, b, k):
        """Start of the arrow into node k: the bucket cell (k=0) or node k-1's pointer dot."""
        if k == 0:
            c = self.cell_center(b)
            return c
        return np.array([self._ptr_x(b), self.node_center(b, k - 1)[1], 0])

    def _arrow(self, b, k):
        start = self._arrow_start(b, k)
        end = np.array([start[0], self.node_center(b, k)[1] + self.node_height / 2, 0])
        return Arrow(start, end, buff=0, stroke_width=3, tip_length=0.15,
                     max_tip_length_to_length_ratio=0.5, color=T.text)

    def chain_bottom(self, b):
        """Lowest y the chain in bucket b reaches (cell bottom when empty)."""
        n = len(self.chains[b])
        if n == 0:
            return self.cell_center(b)[1] - self.cell_size / 2
        return self.node_center(b, n - 1)[1] - self.node_height / 2

    # ---------- access ----------

    def node(self, b, k) -> ChainNode:
        return self.chains[b][k]

    def find(self, value):
        """(bucket, depth) of the first node whose first field is `value`, or None."""
        for b, chain in enumerate(self.chains):
            for k, node in enumerate(chain):
                if node.value == str(value):
                    return b, k
        return None

    def end_marker(self, b):
        """The X a search runs into at the end of bucket b's chain."""
        return self.chains[b][-1].cross if self.chains[b] else self.cell_crosses[b]

    def highlight_cell(self, b, color=None, opacity=0.4) -> Animation:
        color = T.focus if color is None else color
        return self.cells[b].animate.set_fill(color, opacity=opacity)

    def unhighlight_cell(self, b) -> Animation:
        return self.cells[b].animate.set_fill(opacity=0)

    def clear_highlights(self) -> List[Animation]:
        anims = [c.animate.set_fill(opacity=0) for c in self.cells]
        anims += [n.unhighlight() for chain in self.chains for n in chain]
        return anims

    # ---------- mutation ----------

    def _make_node(self, fields):
        fields = fields if isinstance(fields, (tuple, list)) else (fields,)
        return ChainNode(fields, self.field_widths, height=self.node_height, font_size=self.font_size)

    def _rebuild_static(self, b):
        """Not animated: arrows, null markers, and cell dot/X for bucket b."""
        for a in self.arrows[b]:
            self.remove(a)
        self.arrows[b] = [self._arrow(b, k) for k in range(len(self.chains[b]))]
        self.add(*self.arrows[b])
        empty = not self.chains[b]
        self.cell_crosses[b].set_opacity(1 if empty else 0)
        self.cell_dots[b].set_opacity(0 if empty else 1)
        for k, node in enumerate(self.chains[b]):
            node.show_null(k == len(self.chains[b]) - 1)

    def _relink(self, b) -> List[Animation]:
        """Animations re-pointing bucket b after its `chains[b]` list changed:
        old arrows fade out, new ones fade in, nodes slide to their slots."""
        anims: List[Animation] = []
        for a in self.arrows[b]:
            self.remove(a)
            anims.append(FadeOut(a))
        self.arrows[b] = [self._arrow(b, k) for k in range(len(self.chains[b]))]
        for a in self.arrows[b]:
            self.add(a)
            anims.append(FadeIn(a))
        empty = not self.chains[b]
        anims.append(self.cell_crosses[b].animate.set_opacity(1 if empty else 0))
        anims.append(self.cell_dots[b].animate.set_opacity(0 if empty else 1))
        for k, node in enumerate(self.chains[b]):
            # One target per node: a separate .animate on node.cross would fight
            # the node's own move and leave the X behind.
            node.generate_target()
            node.target.move_to(self.node_center(b, k))
            node.target.show_null(k == len(self.chains[b]) - 1)
            anims.append(MoveToTarget(node))
        return anims

    def push_front(self, b, fields, source: Optional[Mobject] = None) -> List[Animation]:
        """New node at the front of bucket b; the rest of the chain slides down.
        With `source` (e.g. a value floating above the table), the node flies in
        from there and `source` fades out on the way."""
        node = self._make_node(fields)
        target = self.node_center(b, 0)
        node.move_to(target)
        node.show_null(not self.chains[b])
        self.chains[b].insert(0, node)
        self.add(node)
        anims = self._relink(b)
        # The node is already at its slot and FadeIn sets its look; drop
        # _relink's animations on it so the two don't fight.
        family = set(node.get_family())
        anims = [a for a in anims if getattr(a, "mobject", None) not in family]
        if source is not None:
            anims.append(FadeIn(node, target_position=source.get_center()))
            anims.append(FadeOut(source, target_position=target))
        else:
            anims.append(FadeIn(node, shift=DOWN * 0.3))
        return anims

    def pop_front(self, b):
        """Detach the front node of bucket b: returns (node, animations). The node
        stays on screen where it is -- the caller moves or fades it."""
        node = self.chains[b].pop(0)
        self.remove(node)
        return node, self._relink(b)

    def remove_at(self, b, k) -> List[Animation]:
        """Unlink and fade out node k of bucket b; the rest of the chain slides up."""
        node = self.chains[b].pop(k)
        self.remove(node)
        return [FadeOut(node)] + self._relink(b)

    def bypass_arrow(self, b, k) -> Animation:
        """Swing the arrow into node k around it to node k+1 (or turn the
        pointer before it into NULL when k is last) -- the 'unlink' beat of a
        linked-list delete, before `remove_at` fades the node and closes the gap."""
        old = self.arrows[b][k]
        if k + 1 < len(self.chains[b]):
            start = self._arrow_start(b, k)
            nxt = self.node_center(b, k + 1)
            end = np.array([self.cell_center(b)[0] + self.node_width / 2, nxt[1], 0])
            new = CurvedArrow(start + RIGHT * 0.05, end, angle=-PI / 2, stroke_width=3,
                              tip_length=0.15, color=T.focus)
            return Transform(old, new)
        return old.animate.set_opacity(0)


__all__ = ["ChainNode", "ChainedHashTable"]
