"""The bounds check: an optional report of layout problems, written while rendering.

    LECTERN_BOUNDS=/tmp/issues.txt manim-slides render -ql lectures/lr_tables.py LrTables

At every slide break, SlideScene appends a line to that file for:

    OFF SCREEN    something extends past the edge of the frame
    OVERLAP       two pieces of text overlap (compared letter by letter)
    LINE THROUGH  a line or arrow runs through text
    SHRINK        page()/panes() had to scale a block down a lot to fit it
    NO ROOM       more() couldn't find space below what's already on screen

It is approximate: it misses some problems and reports some things that look fine
(text on purpose over a shape, say). Use it to find slides worth looking at, not
as proof that a lecture is clean. With LECTERN_BOUNDS unset it does nothing.
"""

import os

import numpy as np
from manim import ArcBetweenPoints, CurvedArrow, Line, MarkupText, Paragraph, SingleStringMathTex, Text, config

__all__ = ["report", "check", "boxes_hit", "name_of"]

ENV = "LECTERN_BOUNDS"

_TEXT = (Text, MarkupText, Paragraph, SingleStringMathTex)


def _title_of(scene):
    t = getattr(scene, "title", None)
    return getattr(t, "original_text", "?") if t is not None else "?"


def report(scene, message):
    path = os.environ.get(ENV)
    if path:
        with open(path, "a") as f:
            f.write(f"{message} | {type(scene).__name__} | {_title_of(scene)}\n")


def check(scene):
    """Report everything on screen that's off the frame, overlapping, or crossed."""
    if not os.environ.get(ENV):
        return
    _check_overlaps(scene)
    hw, hh = config.frame_width / 2 + 0.02, config.frame_height / 2 + 0.02
    for m in scene.mobjects:
        if not m.has_points() and not m.submobjects:
            continue
        try:
            l, r, t, b = m.get_left()[0], m.get_right()[0], m.get_top()[1], m.get_bottom()[1]
        except Exception:  # some mobjects have no bounding box
            continue
        if l < -hw or r > hw or t > hh or b < -hh:
            report(scene, f"OFF SCREEN {type(m).__name__} l={l:.2f} r={r:.2f} t={t:.2f} b={b:.2f}")


def _check_overlaps(scene):
    """Compares individual letters, not whole blocks, so a line of text that clips one
    corner of another still counts. Also finds lines drawn through text."""
    leaves, lines = [], []
    for m in scene.mobjects:
        _text_leaves(m, leaves)
        _line_leaves(m, lines)
    leaves = [m for m in leaves if _visible(m)]
    glyphs = [_glyph_boxes(m) for m in leaves]
    for i in range(len(leaves)):
        for j in range(i + 1, len(leaves)):
            if _glyphs_hit(glyphs[i], glyphs[j]):
                report(scene, f"OVERLAP {name_of(leaves[i])[:40]!r} x {name_of(leaves[j])[:40]!r}")
    for ln in lines:
        pts = ln.get_all_points()
        if len(pts) < 2:
            continue
        samples = np.linspace(pts[0], pts[-1], 60)[:, :2] if type(ln).__name__ in ("Line", "Arrow") else pts[:, :2]
        for t, g in zip(leaves, glyphs):
            if len(g) and _points_in(samples, g).sum() >= 2:
                report(scene, f"LINE THROUGH {name_of(t)[:40]!r}")


def _text_leaves(mob, out):
    if isinstance(mob, _TEXT):
        out.append(mob)
        return
    for sub in mob.submobjects:
        _text_leaves(sub, out)


def _line_leaves(mob, out):
    if isinstance(mob, _TEXT):
        return
    if isinstance(mob, (Line, CurvedArrow, ArcBetweenPoints)) and mob.get_stroke_opacity() > 0.25:
        out.append(mob)
        return
    for sub in mob.submobjects:
        _line_leaves(sub, out)


def name_of(m):
    return str(getattr(m, "original_text", None) or getattr(m, "tex_string", None) or type(m).__name__)


def _glyph_boxes(m):
    boxes = []
    for g in m.family_members_with_points():
        p = g.get_all_points()
        if len(p):
            boxes.append((p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max()))
    return np.array(boxes) if boxes else np.zeros((0, 4))


def _glyphs_hit(a, b, frac=0.15):
    """True if some letter of `a` and some letter of `b` overlap by more than `frac` of
    the smaller one's area."""
    if not len(a) or not len(b):
        return False
    w = np.minimum(a[:, 2][:, None], b[:, 2][None, :]) - np.maximum(a[:, 0][:, None], b[:, 0][None, :])
    h = np.minimum(a[:, 3][:, None], b[:, 3][None, :]) - np.maximum(a[:, 1][:, None], b[:, 1][None, :])
    area_a = (a[:, 2] - a[:, 0]) * (a[:, 3] - a[:, 1])
    area_b = (b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])
    small = np.maximum(np.minimum(area_a[:, None], area_b[None, :]), 1e-4)
    return bool(((w > 0) & (h > 0) & (w * h / small > frac)).any())


def _points_in(points, boxes):
    """For each point, whether it's inside the middle of any box (ignoring a 12% rim)."""
    w, h = boxes[:, 2] - boxes[:, 0], boxes[:, 3] - boxes[:, 1]
    x, y = points[:, 0][:, None], points[:, 1][:, None]
    return ((x > boxes[:, 0] + 0.12 * w) & (x < boxes[:, 2] - 0.12 * w)
            & (y > boxes[:, 1] + 0.12 * h) & (y < boxes[:, 3] - 0.12 * h)).any(axis=1)


def boxes_hit(a, b, gap=0.03):
    """Whether two mobjects' bounding boxes overlap. Empty space inside of a group
    counts, which is the cautious answer."""
    try:
        return (a.get_left()[0] < b.get_right()[0] - gap and b.get_left()[0] < a.get_right()[0] - gap
                and a.get_bottom()[1] < b.get_top()[1] - gap and b.get_bottom()[1] < a.get_top()[1] - gap)
    except Exception:  # some mobjects have no bounding box
        return False


def _visible(m):
    try:
        fam = m.family_members_with_points()
        return len(fam) > 0 and max(x.get_fill_opacity() for x in fam) > 0.3
    except Exception:
        return False
