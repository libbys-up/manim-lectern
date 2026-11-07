"""Doubly linked list visual utilities for Manim.

Static-layout companion to `LinkedList` (linked_list.py): each cell shows a value plus
*two* pointer dots -- prev on the left, next on the right (the previous pointer goes to
the left of the next pointer). Next arrows behave exactly like `LinkedListCell.point_to` (bow above,
wider for a bigger skip). Prev arrows always launch straight up and arc backward to their
target's top-right corner -- the shape a reversed pointer uses, since a prev pointer *is*
a backward pointer.

Unlike `LinkedList`, this has no `add_cell`/`remove_cell`: to show an insertion or a
removal, redraw individual cells' pointers with `set_next_pointer`/`set_prev_pointer`.
Contributions that add the dynamic operations are welcome.
"""

from typing import List, Optional
from manim import *
import numpy as np

from lectern.structures.linked_list import NilCell
from lectern.theme import T


class DoublyLinkedListCell(VGroup):
    """Visual doubly-linked-list cell: value on the left, a wider pointer area on the
    right holding two dots side by side (prev, then next) so both arrows can leave from
    distinct points.

        |<----------------- width ------------------>|
        [        value      | prev-dot   next-dot    ]
                              ^ pointer area, 4*height/3 wide
    """

    def __init__(self, value, width=1.8, height=0.85, font_size=26):
        super().__init__()
        self.width = width
        self.height = height
        self.font_size = font_size
        self.value = value

        self.box = Rectangle(
            width=width, height=height, stroke_color=T.text, stroke_width=2, fill_opacity=0,
        )

        ptr_region = 4 * height / 3
        divider_x = width / 2 - ptr_region
        label_x = -ptr_region / 2
        prev_dot_x = width / 2 - height
        next_dot_x = width / 2 - height / 3

        self.divider = Line(
            np.array([divider_x, height / 2, 0]),
            np.array([divider_x, -height / 2, 0]),
            color=T.text,
        )
        self.label = Text(str(value), font_size=font_size).move_to(np.array([label_x, 0, 0]))
        self.prev_dot = Dot(radius=height / 8, color=T.text).move_to(np.array([prev_dot_x, 0, 0]))
        self.next_dot = Dot(radius=height / 8, color=T.text).move_to(np.array([next_dot_x, 0, 0]))

        self.next_pointer_arrow: Optional[ArcBetweenPoints] = None
        self.prev_pointer_arrow: Optional[ArcBetweenPoints] = None
        self.next_target = None
        self.prev_target = None

        self.add(self.box, self.divider, self.label, self.prev_dot, self.next_dot)

    def set_value(self, value) -> Animation:
        new_label = Text(str(value), font_size=self.font_size).move_to(self.label.get_center())
        anim = Transform(self.label, new_label)
        self.value = value
        self.label = new_label
        return anim

    def set_background(self, color, opacity=0.4) -> Animation:
        return self.box.animate.set_fill(color, opacity=opacity)

    def clear_background(self) -> Animation:
        return self.box.animate.set_fill(opacity=0)

    def highlight(self, color=None) -> Animation:
        color = T.focus if color is None else color
        return self.box.animate.set_fill(color, opacity=0.35)

    def unhighlight(self) -> Animation:
        return self.box.animate.set_fill(opacity=0)

    def _arc(self, existing_arrow, start, end, bow, angle_per_skip, max_angle, skip, tip_length) -> ArcBetweenPoints:
        angle = bow * min(max_angle, angle_per_skip * skip)
        new_arrow = ArcBetweenPoints(start, end, angle=angle)
        new_arrow.add_tip(tip_length=tip_length)
        return new_arrow

    def point_to_next(self, target, start, end, angle_per_skip=PI / 6, max_angle=PI / 2, skip=0,
                       bow=None, tip_length=0.15) -> Animation:
        """(Re)draw the next-pointer arrow. Bows above by default (mirroring
        `LinkedListCell.point_to`'s sign convention: rightward bows up, leftward bows
        down) -- pass an explicit `bow` (+1/-1) to override, e.g. the removal
        walkthrough's node-skipping arrow that deliberately dips *below* the row so it
        doesn't read as another prev-pointer arc."""
        self.next_target = target
        default_bow = -1 if end[0] >= start[0] else 1
        b = default_bow if bow is None else bow
        new_arrow = self._arc(self.next_pointer_arrow, start, end, b, angle_per_skip, max_angle, skip, tip_length)

        if self.next_pointer_arrow is None:
            self.next_pointer_arrow = new_arrow
            self.add(self.next_pointer_arrow)
            return Create(self.next_pointer_arrow)
        return Transform(self.next_pointer_arrow, new_arrow)

    def point_to_prev(self, target, start, end, angle_per_skip=3 * PI / 4, max_angle=3 * PI / 4, skip=1,
                       tip_length=0.15) -> Animation:
        """(Re)draw the prev-pointer arrow. Always uses a wide, skip-agnostic bow
        (the reversed-pointer shape) so it launches straight up from
        the dot and arcs backward into the target, regardless of how far away that
        target is -- a prev pointer only ever reaches the immediately preceding node
        (or, after a removal, the one before that)."""
        self.prev_target = target
        bow = -1 if end[0] >= start[0] else 1
        new_arrow = self._arc(self.prev_pointer_arrow, start, end, bow, angle_per_skip, max_angle, skip, tip_length)

        if self.prev_pointer_arrow is None:
            self.prev_pointer_arrow = new_arrow
            self.add(self.prev_pointer_arrow)
            return Create(self.prev_pointer_arrow)
        return Transform(self.prev_pointer_arrow, new_arrow)


class DoublyLinkedList(VGroup):
    """Static container for doubly-linked cells: builds a fully wired prev/next chain
    from a list of values, flanked by a nil sentinel on each end -- matching the script's
    own notation, `* <- 1 <-> 2 <-> ... <-> n -> *`."""

    def __init__(self, values: Optional[List] = None, cell_width=1.8, cell_height=0.85, gap=0.9,
                 start_point=ORIGIN, font_size=26):
        super().__init__()
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.gap = gap
        self.start_point = np.array(start_point, dtype=float)
        self.font_size = font_size

        if values is None:
            values = []
        self.cells: List[DoublyLinkedListCell] = [
            DoublyLinkedListCell(v, width=cell_width, height=cell_height, font_size=font_size) for v in values
        ]

        nil_size = min(cell_width, cell_height) * 0.5
        self.nil_left = NilCell(size=nil_size)
        self.nil_right = NilCell(size=nil_size)

        self.layout()
        self.add(self.nil_left, *self.cells, self.nil_right)

        for i in range(len(self.cells)):
            # Side effect only: builds & attaches each arrow. The Create these return is
            # never played -- the whole group's later FadeIn is what actually reveals it,
            # matching `LinkedList.__init__`'s identical convention.
            self.set_next_pointer(i, i + 1 if i + 1 < len(self.cells) else None)
            self.set_prev_pointer(i, i - 1 if i > 0 else None)

    def layout(self):
        y = self.start_point[1]
        last_x = self.start_point[0]
        for i, cell in enumerate(self.cells):
            if i == 0:
                cx = self.start_point[0]
            else:
                cx = last_x + self.cell_width / 2 + self.gap + self.cell_width / 2
            cell.move_to(np.array([cx, y, 0]))
            last_x = cx

        left_anchor = self.cells[0].box.get_center()[0] if self.cells else self.start_point[0]
        self.nil_left.move_to(np.array([left_anchor - self.cell_width / 2 - self.gap - self.nil_left.size / 2, y, 0]))

        right_anchor = last_x if self.cells else self.start_point[0]
        self.nil_right.move_to(np.array([right_anchor + self.cell_width / 2 + self.gap + self.nil_right.size / 2, y, 0]))

    def _skip_count(self, i, j) -> int:
        return max(0, abs(j - i) - 1)

    def set_next_pointer(self, index, target_index: Optional[int] = None, skip=None, bow=None,
                          angle_per_skip=PI / 6, max_angle=PI / 2, tip_length=0.15) -> Animation:
        """Point cell `index`'s next arrow at cell `target_index` (nil_right if None).
        `skip` overrides the auto (index-gap) count -- useful once a between cell has
        been logically removed but is still visually present. See `point_to_next` for
        `bow`."""
        n = len(self.cells)
        ti = n if target_index is None else target_index
        target = self.nil_right if target_index is None else self.cells[target_index]
        end = self.nil_right.get_left() if target_index is None else self.cells[target_index].box.get_left()
        sk = self._skip_count(index, ti) if skip is None else skip

        return self.cells[index].point_to_next(
            target, start=self.cells[index].next_dot.get_center(), end=end,
            angle_per_skip=angle_per_skip, max_angle=max_angle, skip=sk, bow=bow, tip_length=tip_length,
        )

    def set_prev_pointer(self, index, target_index: Optional[int] = None, skip=1,
                          angle_per_skip=3 * PI / 4, max_angle=3 * PI / 4, tip_length=0.15) -> Animation:
        """Point cell `index`'s prev arrow at cell `target_index` (nil_left if None)."""
        target = self.nil_left if target_index is None else self.cells[target_index]
        end = self.nil_left.get_left() if target_index is None else self.cells[target_index].box.get_corner(UR)

        return self.cells[index].point_to_prev(
            target, start=self.cells[index].prev_dot.get_center(), end=end,
            angle_per_skip=angle_per_skip, max_angle=max_angle, skip=skip, tip_length=tip_length,
        )

    def __getitem__(self, index) -> DoublyLinkedListCell:
        return self.cells[index]

    def __len__(self):
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def highlight_cell(self, index, color=None) -> Animation:
        color = T.focus if color is None else color
        return self.cells[index].highlight(color)

    def unhighlight_cell(self, index) -> Animation:
        return self.cells[index].unhighlight()

    def set_background_cell(self, index, color, opacity=0.4) -> Animation:
        return self.cells[index].set_background(color, opacity=opacity)

    def clear_background_cell(self, index) -> Animation:
        return self.cells[index].clear_background()


__all__ = ["DoublyLinkedListCell", "DoublyLinkedList"]
