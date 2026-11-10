"""Linked list visual utilities for Manim.

This module implements a singly linked list visualization where each cell is
rendered as a box with a left value field, a vertical divider, and a right pointer
area containing a dot and an arrow to the next cell. Nil is shown as a square
with an X. Pointers are drawn as arcs that bow above the cells, so a pointer can
visually pass over an intermediate cell (e.g. while animating a node's removal).

Pointer-arc endpoints are always computed analytically from cell indices (not
read off live mobject coordinates), since a cell's on-screen position may still
be mid-animation (queued via `.animate`, not yet applied) at the moment a pointer
needs to be (re)drawn to where that cell is headed.
"""

from typing import List, Optional
from manim import *
import numpy as np
from lectern.theme import T
from lectern.alt import AltText, count, describe_tree, words


class LinkedListCell(VGroup):
    """Visual singly-linked-list cell: a single width x height box with a value on
    the left and a height x height pointer square (divider + dot) at the right end.

        |<---------- width ---------->|
        [        value      | pointer ]
                              ^ height-wide square, dot centered in it
    """

    def __init__(self, value, width=1.6, height=0.9, font_size=24):
        super().__init__()
        self.width = width
        self.height = height
        self.font_size = font_size
        self.value = value

        self.box = Rectangle(
            width=width,
            height=height,
            stroke_color=T.text,
            stroke_width=2,
            fill_opacity=0,
        )

        divider_x = width / 2 - 2*height/3
        self.divider = Line(
            np.array([divider_x, height / 2, 0]),
            np.array([divider_x, -height / 2, 0]),
            color=T.text,
        )

        label_x = -height / 3
        dot_x = width / 2 - height / 3

        self.label = Text(str(value), font_size=font_size).move_to(np.array([label_x, 0, 0]))
        self.dot = Dot(radius=height/8, color=T.text).move_to(np.array([dot_x, 0, 0]))

        self.pointer_arrow: Optional[ArcBetweenPoints] = None
        self.next_target = None
        # True between hide_pointer and reveal_pointer -- point_to keeps a
        # hidden arrow hidden when it's retargeted, instead of fading it back in.
        self.pointer_hidden = False

        self.add(self.box, self.divider, self.label, self.dot)

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

    def hide_pointer(self) -> Animation:
        """Fade this cell's pointer arrow to invisible in place, leaving its
        `next_target` bookkeeping untouched. A later `point_to` call (e.g. via
        `LinkedList.add_cell`/`remove_cell`'s pointer refresh, which `Transform`s
        the existing arrow rather than replacing it) will fade it back in as it
        moves to its new, correct position while staying hidden, until
        `reveal_pointer` -- used for the insertion-sort visual of "cutting" a
        pointer while descending, then reconnecting it as the recursion returns."""
        self.pointer_hidden = True
        return self.pointer_arrow.animate.set_opacity(0)

    def reveal_pointer(self) -> Animation:
        """Fade this cell's pointer arrow back to fully visible in place --
        the counterpart to `hide_pointer`, for restoring a "cut" pointer one
        at a time (e.g. in reverse cut order) without needing to recompute
        its endpoints (any retargeting while hidden already moved it)."""
        self.pointer_hidden = False
        return self.pointer_arrow.animate.set_opacity(1)

    def point_to(self, target, start, end, angle_per_skip=PI / 6, max_angle=PI / 2, skip=0, tip_length=0.15) -> Animation:
        """(Re)draw the pointer arrow from explicit `start`/`end` points (the caller computes
        these analytically) to `target`, bowing upward more the more cells it skips over."""
        self.next_target = target
        # ArcBetweenPoints bows *away* from a positive angle in the rotational
        # (counterclockwise) sense, which flips depending on the chord's own
        # direction -- so a rightward chord needs a negative angle to bow
        # upward, and a leftward chord needs a positive one. Getting this
        # backwards is what makes an arrow curve down into the cells it's
        # supposed to arc over.
        bow = -1 if end[0] >= start[0] else 1
        angle = bow * min(max_angle, angle_per_skip * skip)
        # Build via ArcBetweenPoints + add_tip(tip_length=...) rather than CurvedArrow
        # directly, since CurvedArrow always adds a tip at its (larger) default size.
        new_arrow = ArcBetweenPoints(start, end, angle=angle)
        new_arrow.add_tip(tip_length=tip_length)
        if self.pointer_hidden:
            new_arrow.set_opacity(0)

        if self.pointer_arrow is None:
            self.pointer_arrow = new_arrow
            self.add(self.pointer_arrow)
            return Create(self.pointer_arrow)
        # Mutate the existing (already on-screen, parented) arrow in place via Transform.
        # Do NOT reassign self.pointer_arrow to new_arrow -- new_arrow is never added to
        # the scene, and a later Transform sourced from it would get auto-added by Manim
        # as a *second*, disconnected arrow, leaving the real one stale on screen.
        return Transform(self.pointer_arrow, new_arrow)


class NilCell(VGroup):
    """Visual sentinel representing nil as a square with an X."""

    def __init__(self, size=0.6):
        super().__init__()
        self.size = size
        self.box = Square(side_length=size, stroke_color=T.text, stroke_width=2, fill_opacity=0)
        self.line1 = Line(self.box.get_corner(UL), self.box.get_corner(DR), color=T.text)
        self.line2 = Line(self.box.get_corner(UR), self.box.get_corner(DL), color=T.text)
        self.add(self.box, self.line1, self.line2)

    def get_left(self):
        return self.box.get_left()

    def get_top(self):
        return self.box.get_top()

    def set_background(self, color, opacity=0.4) -> Animation:
        return self.box.animate.set_fill(color, opacity=opacity)

    def clear_background(self) -> Animation:
        return self.box.animate.set_fill(opacity=0)


class LinkedList(AltText, VGroup):
    """Container for linked list cells with insertion, deletion, and pointer rewiring."""

    def __init__(self, values: Optional[List] = None, cell_width=1.6, cell_height=0.9, gap=0.4,
                 start_point=ORIGIN, font_size=24, cell_widths: Optional[List[float]] = None,
                 tip_length=0.15):
        super().__init__()
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.gap = gap
        self.start_point = start_point
        self.font_size = font_size
        self.tip_length = tip_length

        self.cells: List[LinkedListCell] = []
        self.cell_widths: List[float] = []
        self.nil = NilCell(size=min(cell_widths[0] if cell_widths else cell_width, cell_height) * 0.5)
        self.add(self.nil)

        if values is None:
            values = []
        for i, value in enumerate(values):
            width = cell_widths[i] if cell_widths is not None else cell_width
            cell = LinkedListCell(value, width=width, height=cell_height, font_size=font_size)
            self.cells.append(cell)
            self.cell_widths.append(width)
            self.add(cell)

        self.layout()
        for i, cell in enumerate(self.cells):
            cell.next_target = self._target_for(i)
            self._refresh_pointer(i)

    def describe(self):
        """Follows the next pointers from the first cell, so a rewired list reads in
        its new order."""
        if not self.cells:
            return "An empty linked list."
        vals, seen, node = [], set(), self.cells[0]
        while node is not None and node is not self.nil and id(node) not in seen:
            seen.add(id(node))
            vals.append(str(node.value))
            node = node.next_target
        end = "null" if node is None or node is self.nil else f"back to {node.value}"
        return f"A linked list: {', then '.join(vals)}, then {end}."

    def _slot_width(self, index):
        """Width of the box occupying `index` (a real cell, or nil past the end)."""
        if index < len(self.cell_widths):
            return self.cell_widths[index]
        return self.nil.size

    def _cell_position(self, index):
        left_edge = self.start_point[0] - self._slot_width(0) / 2
        for j in range(index):
            left_edge += self._slot_width(j) + self.gap
        x = left_edge + self._slot_width(index) / 2
        return np.array([x, self.start_point[1], 0])

    def _slot_size(self, index):
        """Width/height of the box occupying `index` (a real cell, or nil past the end)."""
        if index < len(self.cells):
            return self.cell_widths[index], self.cell_height
        return self.nil.size, self.nil.size

    def _dot_point(self, index):
        """Center of the pointer dot for the cell at `index` (start of its arrow)."""
        w, h = self._slot_size(index)
        return self._cell_position(index) + RIGHT * (w / 2 - h / 3)

    def _front_point(self, index):
        """Left edge, vertical center -- where a forward-pointing arrow arrives."""
        w, _h = self._slot_size(index)
        return self._cell_position(index) + LEFT * (w / 2)

    def _front_right_corner(self, index):
        """Top-right corner -- where a backward-pointing arrow arrives."""
        w, h = self._slot_size(index)
        return self._cell_position(index) + RIGHT * (w / 2) + UP * (h / 2)

    def _pointer_endpoint(self, source_index, target_index):
        if target_index < source_index:
            return self._front_right_corner(target_index)
        return self._front_point(target_index)

    def layout(self):
        for i, cell in enumerate(self.cells):
            cell.move_to(self._cell_position(i))
        self.nil.move_to(self._cell_position(len(self.cells)))

    def _move_to_animation(self, cell, target_position) -> Animation:
        """Shift `cell` so its *box* (not its VGroup bounding box) ends up at
        `target_position`. A cell's pointer arrow is a child of its VGroup and extends
        out toward its target, asymmetrically skewing the group's bounding-box center
        -- so `cell.animate.move_to(...)` would mis-place the box itself. A `shift` by
        the box's own current-position delta is unaffected by that skew."""
        delta = np.array(target_position) - cell.box.get_center()
        return cell.animate.shift(delta)

    def _target_for(self, index):
        return self.cells[index + 1] if index + 1 < len(self.cells) else self.nil

    def _skip_count(self, source_index, target_index) -> int:
        return max(0, abs(target_index - source_index) - 1)

    def _index_of(self, target) -> int:
        return len(self.cells) if target is self.nil else self.cells.index(target)

    def _refresh_pointer(self, index) -> Optional[Animation]:
        """(Re)draw a cell's pointer arrow using analytically-computed endpoints for its
        own index and whatever it logically points at, regardless of any pending
        (not-yet-played) position animation on either cell."""
        cell = self.cells[index]
        target = cell.next_target
        if target is None:
            return None
        target_index = self._index_of(target)
        skip = self._skip_count(index, target_index)
        start = self._dot_point(index)
        end = self._pointer_endpoint(index, target_index)
        return cell.point_to(target, start, end, skip=skip, tip_length=self.tip_length)

    def __getitem__(self, index) -> LinkedListCell:
        return self.cells[index]

    def __len__(self):
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def add_cell(self, value, index: Optional[int] = None, fade=True) -> List[Animation]:
        if index is None:
            index = len(self.cells)

        new_cell = LinkedListCell(value, width=self.cell_width, height=self.cell_height, font_size=self.font_size)
        self.cells.insert(index, new_cell)
        self.cell_widths.insert(index, self.cell_width)
        new_cell.move_to(self._cell_position(index))
        self.add(new_cell)

        anims: List[Animation] = [
            self._move_to_animation(cell, self._cell_position(i))
            for i, cell in enumerate(self.cells)
            if i > index
        ]
        anims.append(self._move_to_animation(self.nil, self._cell_position(len(self.cells))))

        new_cell.next_target = self._target_for(index)
        # Side effect only: builds & attaches new_cell's pointer arrow. We don't play
        # its Create animation -- combining it with FadeIn(new_cell, ...) below would
        # animate overlapping mobjects (the arrow is a child of new_cell) in the same
        # play() call, which corrupts the arrow's final position. Instead the arrow
        # just fades in as part of the whole new_cell group.
        self._refresh_pointer(index)

        if index > 0:
            self.cells[index - 1].next_target = new_cell
            anims.append(self._refresh_pointer(index - 1))

        for i in range(len(self.cells)):
            if i not in (index, index - 1):
                refreshed = self._refresh_pointer(i)
                if refreshed is not None:
                    anims.append(refreshed)

        if fade:
            anims.insert(0, FadeIn(new_cell, shift=RIGHT))
        # else: appear instantly -- new_cell and its pointer arrow are already
        # added to the scene with no entrance animation.

        return anims

    def remove_cell(self, index: int, fade=True) -> List[Animation]:
        removed = self.cells.pop(index)
        self.cell_widths.pop(index)

        # If some other cell's pointer still targets the removed cell (i.e. the caller
        # didn't explicitly reroute it via set_pointer first), bridge it to whatever the
        # removed cell itself pointed at, so the list stays structurally valid.
        for cell in self.cells:
            if cell.next_target is removed:
                cell.next_target = removed.next_target

        anims: List[Animation] = [
            self._move_to_animation(cell, self._cell_position(i))
            for i, cell in enumerate(self.cells)
            if i >= index
        ]
        anims.append(self._move_to_animation(self.nil, self._cell_position(len(self.cells))))

        for i in range(len(self.cells)):
            refreshed = self._refresh_pointer(i)
            if refreshed is not None:
                anims.append(refreshed)

        # Detach `removed` from the group now rather than relying on FadeOut's
        # remover=True (which only unregisters it from the *scene*, not from
        # this VGroup's own submobjects): left attached, it rides along as an
        # invisible structural child, and a later whole-group FadeOut/Transform
        # (e.g. an `end_slide`) re-derives its starting opacity during family
        # alignment and visibly pops it back into view partway through, before
        # fading out again. Detaching before its own fade animation plays is
        # safe -- `self.play` auto-tracks any mobject an animation targets even
        # once it's no longer nested under `self`.
        self.remove(removed)

        if fade:
            anims.insert(0, removed.animate.set_opacity(0))

        return anims

    def set_pointer(self, index: int, target: Optional[int] = None, angle_per_skip=PI / 6, max_angle=PI / 2) -> Animation:
        target_index = len(self.cells) if target is None else target
        target_cell = self.nil if target is None else self.cells[target]
        self.cells[index].next_target = target_cell

        skip = self._skip_count(index, target_index)
        start = self._dot_point(index)
        end = self._pointer_endpoint(index, target_index)
        return self.cells[index].point_to(
            target_cell, start, end, angle_per_skip=angle_per_skip, max_angle=max_angle, skip=skip,
            tip_length=self.tip_length,
        )

    def cut_pointer(self, index) -> Animation:
        return self.cells[index].hide_pointer()

    def reveal_pointer(self, index) -> Animation:
        return self.cells[index].reveal_pointer()

    def reorder(self, new_order: List[int]) -> List[Animation]:
        """Rearrange cells into `new_order` (a permutation of the current
        cell indices) by moving each cell's own box/label/pointer to its new
        slot, instead of transforming values in place -- e.g. for "sort this
        half" steps that should show nodes physically moving into sorted
        order. Every pointer arrow (including the last cell's arrow to
        `nil`) is redrawn to match the new arrangement."""
        old_cells = self.cells
        old_widths = self.cell_widths
        moves = [
            self._move_to_animation(old_cells[old_i], self._cell_position(new_i))
            for new_i, old_i in enumerate(new_order)
        ]

        self.cells = [old_cells[old_i] for old_i in new_order]
        self.cell_widths = [old_widths[old_i] for old_i in new_order]
        for i, cell in enumerate(self.cells):
            cell.next_target = self._target_for(i)

        pointer_updates = [self._refresh_pointer(i) for i in range(len(self.cells))]
        moves.extend(a for a in pointer_updates if a is not None)
        return moves

    def highlight_cell(self, index, color=None) -> Animation:
        color = T.focus if color is None else color
        return self.cells[index].highlight(color)

    def unhighlight_cell(self, index) -> Animation:
        return self.cells[index].unhighlight()

    def set_background_cell(self, index, color, opacity=0.4) -> Animation:
        return self.cells[index].set_background(color, opacity=opacity)

    def clear_background_cell(self, index) -> Animation:
        return self.cells[index].clear_background()


__all__ = ["LinkedListCell", "NilCell", "LinkedList"]
