from typing import List

from manim import *

from lectern.structures.array import ArrayCell
from lectern.theme import T
from lectern.alt import AltText, count, describe_tree, words


class Stack(AltText, VGroup):
    """Visual stack: a column of ArrayCells growing downward, top to bottom."""

    def __init__(
        self,
        values,
        cell_width=3.0,
        cell_height=1.0,
        gap=0,
        start_point=ORIGIN,
        font_size=24,
    ):
        super().__init__()
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.gap = gap
        self.start_point = start_point
        self.font_size = font_size

        self.cells: List[ArrayCell] = []

        for value in values:
            cell = ArrayCell(value, width=cell_width, height=cell_height, font_size=font_size)
            self.cells.append(cell)
            self.add(cell)

        self.layout()

    def describe(self):
        if not self.cells:
            return "An empty stack."
        vals = [str(c.value) for c in reversed(self.cells)]
        return f"A stack of {count(len(vals), 'value')}, from the top: {', '.join(vals)}."

    def _cell_position(self, index):
        return self.start_point + DOWN * index * (self.cell_height + self.gap)

    def layout(self):
        for i, cell in enumerate(self.cells):
            cell.move_to(self._cell_position(i))

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

    def push(self, value) -> List[Animation]:
        index = len(self.cells)
        cell = ArrayCell(value, width=self.cell_width, height=self.cell_height, font_size=self.font_size)
        cell.move_to(self._cell_position(index))

        self.cells.append(cell)
        self.add(cell)

        return [FadeIn(cell)]

    def pop(self) -> Animation:
        cell = self.cells.pop()
        self.remove(cell)
        return FadeOut(cell)

    def add_stack_frame(self, start_index, end_index, label, font_size=24, buff=0.2) -> VGroup:
        group = VGroup(*self.cells[start_index:end_index + 1])
        brace = Brace(group, direction=RIGHT, buff=buff)
        text = Text(label, font_size=font_size).next_to(brace, RIGHT, buff=buff)

        frame = VGroup(brace, text)
        self.add(frame)
        return frame


__all__ = ["Stack"]
