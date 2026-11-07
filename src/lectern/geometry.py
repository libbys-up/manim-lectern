"""Small geometry helpers for attaching lines and arrows to shapes."""

import numpy as np

__all__ = ["box_point", "circle_point"]


def box_point(mob, direction):
    """Where a ray from `mob`'s center in `direction` leaves its bounding box
    (plus a small gap), so an edge stops at the box instead of its center."""
    w, h = mob.width / 2 + 0.03, mob.height / 2 + 0.03
    dx, dy = direction[0], direction[1]
    t = min(w / abs(dx) if abs(dx) > 1e-6 else 1e9, h / abs(dy) if abs(dy) > 1e-6 else 1e9)
    return mob.get_center() + np.array([dx * t, dy * t, 0])


def circle_point(mob, direction):
    """Where a ray from `mob`'s center in `direction` leaves the circle that fits its width."""
    r = mob.width / 2 + 0.02
    return mob.get_center() + r * direction / np.linalg.norm(direction)
