"""Translated from scripts/linear_search.md. Render from the examples folder:

    manim-slides render -ql lectures/linear_search.py LinearSearch
"""

from manim import *
from lectern import *

VALUES = [3, 7, 2, 9, 4]
TARGET = 9


class LinearSearch(SlideScene):
    def construct(self):
        a = Array(VALUES)
        goal = self.styled(f"Looking for **{TARGET}**")
        self.page("Linear Search",
            "* Walk through the array and check each value",
            "* Stop as soon as we find a match",
            N("This is the search you'd do by hand on an unsorted list."),
            P,
            C(goal),
            C(a),
            lambda: self.search(a),
        )

        self.page("How long does it take?",
            r"* Best case: the first value matches, so $\mathcal{O}\left(1\right)$",
            r"* Worst case: no value matches, so we check all $n$, $\mathcal{O}\left(n\right)$",
            P,
            C(self.definition_box("Linear time", [
                "An algorithm takes *linear time* when its work grows in proportion to $n$."])),
        )

        self.recap_page(
            "* Linear search checks each value in order",
            r"* It takes $\mathcal{O}\left(n\right)$ time in the worst case",
        )
        self.pause()

    def search(self, a):
        """Check each cell in turn: highlight it, then mark it rejected or found."""
        for i, value in enumerate(VALUES):
            self.pause()
            self.play(a.set_background_cell(i, T.focus))
            if value == TARGET:
                # STYLE.md: never color alone, so a match gets a check mark too.
                mark = Text("✓", color=T.good, font_size=36).next_to(a.cells[i], DOWN)
                self.play(a.set_background_cell(i, T.good), FadeIn(mark))
                self.note("Three comparisons failed before this one succeeded.")
                return
            mark = Text("✗", color=T.bad, font_size=36).next_to(a.cells[i], DOWN)
            self.play(a.set_background_cell(i, T.muted), FadeIn(mark))
