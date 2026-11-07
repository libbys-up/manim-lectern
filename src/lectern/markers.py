"""Markers for the item lists that `page()`, `panes()`, and `more()` take.

    self.page("Title",
        "Some text with *emphasis* and `code`.",
        P,                        # \\pause
        "* a bullet",
        "  * a sub-bullet",
        N("Said aloud, not shown."),
        C(self.code(SRC)),        # centered
        H(table),                 # placed now, revealed later
        lambda: self.hl(c, "x"),  # anything callable runs at that point
    )
"""

__all__ = ["P", "N", "C", "H"]


class _Pause:
    def __repr__(self):
        return "P"


P = _Pause()
"""`\\pause`: advance to the next slide without fading anything."""


class N:
    """A speaker note: said aloud, not shown. `manim-slides present` shows notes
    in the presenter view (press S)."""

    def __init__(self, text):
        self.text = text


class C:
    """Center this item horizontally in its region."""

    def __init__(self, mob):
        self.mob = mob


class H:
    """Lay this item out with the others, but don't reveal it. Show it (or pieces of
    it) later, e.g. with `self.rows(table)`."""

    def __init__(self, mob, center=True):
        self.mob = mob
        self.center = center
