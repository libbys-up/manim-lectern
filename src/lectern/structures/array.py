from typing import List

from manim import *
from lectern.theme import T


class ArrayCell(VGroup):
    """Visual array cell: a labeled box holding a single value."""

    def __init__(self, value, width=1.0, height=1.0, font_size=24, color=None):
        color = T.text if color is None else color
        super().__init__()
        self.width = width
        self.height = height
        self.font_size = font_size
        self.value = value
        # `color` is the cell's own foreground (box stroke + label); it defaults to
        # the theme's text color.
        self.color = color

        self.box = Rectangle(
            width=width,
            height=height,
            stroke_color=color,
            stroke_width=2,
            fill_opacity=0,
        )
        self.label = Text(str(value), font_size=font_size, color=color)
        self.label.move_to(self.box.get_center())

        self.add(self.box, self.label)

    def set_value(self, new_value) -> Animation:
        new_label = Text(str(new_value), font_size=self.font_size, color=self.color).move_to(self.box.get_center())
        anim = ReplacementTransform(self.label, new_label)
        self.value = new_value
        self.label = new_label
        return anim

    def fade_value(self, new_value):
        old_label = self.label
        new_label = Text(str(new_value), font_size=self.font_size, color=self.color).move_to(self.box.get_center())
        self.remove(old_label)
        self.add(new_label)
        self.value = new_value
        self.label = new_label
        return FadeOut(old_label), FadeIn(new_label)

    def set_box_width(self, new_width):
        """Resize the cell's box in place (no animation) and re-center it under the label."""
        self.box.stretch_to_fit_width(new_width)
        self.width = new_width

    def highlight(self, color=None, opacity=0.35) -> Animation:
        color = T.focus if color is None else color
        return self.box.animate.set_fill(color, opacity=opacity)

    def unhighlight(self) -> Animation:
        return self.box.animate.set_fill(opacity=0)

    def set_background(self, color, opacity=0.4) -> Animation:
        return self.box.animate.set_fill(color, opacity=opacity)

    def clear_background(self) -> Animation:
        return self.box.animate.set_fill(opacity=0)


class Array(VGroup):
    """Visual array: a row of ArrayCells with optional index labels below."""

    def __init__(
        self,
        values,
        cell_width=1.0,
        cell_height=1.0,
        gap=0,
        start_point=ORIGIN,
        show_indices=False,
        index_font_size=18,
        cell_widths=None,
        font_size=24,
        color=None,
    ):
        color = T.text if color is None else color
        super().__init__()
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.gap = gap
        self.start_point = start_point
        self.index_font_size = index_font_size
        self.font_size = font_size
        self._indices_visible = show_indices
        self.color = color

        self.cells: List[ArrayCell] = []
        self.indices: List[Text] = []
        self.cell_widths: List[float] = []

        for i, value in enumerate(values):
            width = cell_widths[i] if cell_widths is not None else cell_width
            cell = ArrayCell(value, width=width, height=cell_height, font_size=font_size, color=color)
            index_label = Text(str(len(self.cells)), font_size=index_font_size, color=color)
            index_label.set_opacity(1 if show_indices else 0)
            self.cells.append(cell)
            self.cell_widths.append(width)
            self.indices.append(index_label)
            self.add(cell, index_label)

        self.layout()

    def _cell_position(self, index):
        left_edge = self.start_point[0] - self.cell_widths[0] / 2
        for w in self.cell_widths[:index]:
            left_edge += w + self.gap
        x = left_edge + self.cell_widths[index] / 2
        return np.array([x, self.start_point[1], self.start_point[2]])

    def layout(self):
        for i, cell in enumerate(self.cells):
            cell.move_to(self._cell_position(i))
            self.indices[i].move_to(cell.get_bottom() + DOWN * 0.3)

    def set_cell_width(self, index, new_width):
        """Resize a single cell and relayout the row around it.

        Not animated -- call before the array is first shown (like the
        sizes passed to the constructor), not mid-`self.play` sequence.
        """
        self.cell_widths[index] = new_width
        self.cells[index].set_box_width(new_width)
        self.layout()

    def __getitem__(self, index) -> ArrayCell:
        return self.cells[index]

    def __len__(self):
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def set_value(self, index, new_value) -> Animation:
        return self.cells[index].set_value(new_value)

    def fade_value(self, index, new_value):
        return self.cells[index].fade_value(new_value)

    def highlight_cell(self, index, color=None) -> Animation:
        color = T.focus if color is None else color
        return self.cells[index].highlight(color)

    def unhighlight_cell(self, index) -> Animation:
        return self.cells[index].unhighlight()

    def set_background_cell(self, index, color, opacity=0.4) -> Animation:
        return self.cells[index].set_background(color, opacity=opacity)

    def clear_background_cell(self, index) -> Animation:
        return self.cells[index].clear_background()

    def highlight_range(self, start, end, color=None) -> List[Animation]:
        color = T.focus if color is None else color
        return [cell.highlight(color) for cell in self.cells[start:end]]

    def unhighlight_range(self, start, end) -> List[Animation]:
        return [cell.unhighlight() for cell in self.cells[start:end]]

    def set_background_range(self, start, end, color, opacity=0.4) -> List[Animation]:
        return [cell.set_background(color, opacity=opacity) for cell in self.cells[start:end]]

    def clear_background_range(self, start, end) -> List[Animation]:
        return [cell.clear_background() for cell in self.cells[start:end]]

    def append_value(self, value, width=None) -> List[Animation]:
        index = len(self.cells)
        width = width if width is not None else self.cell_width
        cell = ArrayCell(value, width=width, height=self.cell_height, font_size=self.font_size, color=self.color)
        index_label = Text(str(index), font_size=self.index_font_size, color=self.color)
        index_label.set_opacity(1 if self._indices_visible else 0)

        self.cells.append(cell)
        self.cell_widths.append(width)
        self.indices.append(index_label)
        self.add(cell, index_label)
        self.layout()

        anims: List[Animation] = [FadeIn(cell)]
        if self._indices_visible:
            anims.append(FadeIn(index_label))
        return anims

    def pop_value(self) -> List[Animation]:
        """Remove and fade out the rightmost cell -- mirrors `append_value`,
        giving `Array` push/pop stack semantics that grow left-to-right
        (fade in on the right to push, fade out the rightmost to pop)."""
        cell = self.cells.pop()
        self.cell_widths.pop()
        index_label = self.indices.pop()
        self.remove(cell, index_label)

        anims: List[Animation] = [FadeOut(cell)]
        if self._indices_visible:
            anims.append(FadeOut(index_label))
        return anims

    def dequeue_value(self) -> List[Animation]:
        """Remove and fade out the leftmost cell, then slide every remaining
        cell (and its index label, if shown) left to close the gap --
        mirrors `pop_value`, but gives `Array` FIFO queue semantics (fade in
        on the right to enqueue, fade out the leftmost and compact left to
        dequeue) instead of `pop_value`'s stack semantics."""
        cell = self.cells.pop(0)
        self.cell_widths.pop(0)
        index_label = self.indices.pop(0)
        self.remove(cell, index_label)

        anims: List[Animation] = [FadeOut(cell)]
        if self._indices_visible:
            anims.append(FadeOut(index_label))

        for i, remaining_cell in enumerate(self.cells):
            target = self._cell_position(i)
            anims.append(remaining_cell.animate.move_to(target))
            if self._indices_visible:
                anims.append(self.indices[i].animate.move_to(target + DOWN * (self.cell_height / 2 + 0.3)))
        return anims

    def move_out(self, index, point, path_arc=0) -> Animation:
        return self.cells[index].label.animate(path_arc=path_arc).move_to(point)

    def move_in(self, index, path_arc=0) -> Animation:
        cell = self.cells[index]
        return cell.label.animate(path_arc=path_arc).move_to(cell.box.get_center())

    def swap(self, i, j, arc_angle=PI / 2) -> List[Animation]:
        cell_i = self.cells[i]
        cell_j = self.cells[j]
        pos_i = cell_i.box.get_center()
        pos_j = cell_j.box.get_center()

        anims = [
            cell_i.label.animate(path_arc=arc_angle).move_to(pos_j),
            cell_j.label.animate(path_arc=arc_angle).move_to(pos_i),
        ]
        cell_i.label, cell_j.label = cell_j.label, cell_i.label
        cell_i.value, cell_j.value = cell_j.value, cell_i.value
        return anims

    def toggle_indices(self, show: bool) -> Animation:
        self._indices_visible = show
        opacity = 1 if show else 0
        return VGroup(*self.indices).animate.set_opacity(opacity)

    def set_index_label(self, index, value) -> Animation:
        old_label = self.indices[index]
        new_label = Text(str(value), font_size=self.index_font_size, color=self.color).move_to(old_label.get_center())
        new_label.set_opacity(1 if self._indices_visible else 0)
        anim = ReplacementTransform(old_label, new_label)
        self.indices[index] = new_label
        return anim

    def add_pointer(self, source_index, target_index, text, font_size=24, lift=0.6) -> tuple[Animation, Animation]:
        source_box = self.cells[source_index].box
        target_box = self.cells[target_index].box

        #label = Text(text, font_size=font_size)
        #label.next_to(source_box, UP, buff=lift)
        rep = self.cells[source_index].set_value(text)

        start = source_box.get_top()
        end = target_box.get_top()
        direction = -1 if end[0] >= start[0] else 1
        arrow = CurvedArrow(start, end, angle=direction * PI / 2, color=self.color)

        self.add(arrow)
        return rep, Create(arrow)


__all__ = ["ArrayCell", "Array"]
