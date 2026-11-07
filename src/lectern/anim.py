"""Animations that implement the "values move" rule in conventions/STYLE.md.

When a value goes from one place to another, the viewer should see it travel:

    self.play(arrive(cell.value, new_value, src=register.value))

A copy of `src` moves to where the new value goes and becomes it, while the old
value fades. `src` can be several things (a list or VGroup): their copies merge
into the result, like the two operands of an add.
"""

from manim import Transform, VGroup

__all__ = ["Arrive", "arrive"]


class Arrive(Transform):
    """A copy of `src` (something on screen) moves to where `new` goes, and becomes
    it, while `old` fades. Afterwards `old` *is* the new value (it took `new`'s
    shape), so code holding a reference to the cell's value mobject keeps working,
    and the moving copy is gone."""

    def __init__(self, old, new, src, **kwargs):
        self.old = old
        # A value held on screen by SlideScene.carry() is consumed by the move.
        self.carried = src if getattr(src, "carried", False) else None
        self.fly = src.copy()
        super().__init__(self.fly, new, **kwargs)

    def _setup_scene(self, scene):
        super()._setup_scene(scene)
        if self.carried is not None:  # the held value is the one that moves now
            scene.remove(self.carried)

    def interpolate_mobject(self, alpha):
        super().interpolate_mobject(alpha)
        self.old.set_opacity(1 - self.rate_func(alpha))

    def clean_up_from_scene(self, scene):
        # Transform leaves the moving copy on screen with the new value's shape.
        # Hand that shape to `old`, the mobject the caller keeps, and drop the copy.
        super().clean_up_from_scene(scene)
        self.old.become(self.target_mobject)
        scene.remove(self.fly)


def arrive(old, new, src=None):
    """`old` becomes `new`. With `src`, a copy of `src` carries the value there (see
    `Arrive`). Without one, `old` simply transforms, which STYLE.md allows only
    for starting states, hypotheticals, and a variable updating itself."""
    if src is None:
        return Transform(old, new)
    if isinstance(src, (list, tuple)):
        src = VGroup(*src)
    return Arrive(old, new, src)
