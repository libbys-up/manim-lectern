"""Code blocks, and highlighting parts of them.

Build a block from a string, then point at lines or pieces of it by line number
(1-indexed) or by text that appears on the line:

    c = self.code('''
        int sum = 0;
        for (int i = 0; i < n; i++)
        {
            sum += a[i];
        }
    ''', lang="java")
    self.hl(c, 2)            # highlight line 2
    self.hl(c, "sum +=")     # highlight the line containing "sum +="
    self.hls(c, "i++")       # highlight just "i++"

Inside the source:
    //: text      a comment line in a different color (for notes on code)
    ⟦ ... ⟧       a placeholder, drawn in the theme's `bad` color (for templates)

Languages Pygments doesn't know (MIPS assembly, say) can be colored by registering
a painter; see `register_painter` and lectern.extras.assembly.mips.

Two highlighters live here:
- the `hl*` methods of `CodeMixin` draw a filled background behind the target, and
- `CodeHighlighter` draws an outline. It works on code built from a file
  (`SlideScene.code_block`), and is what the data structures lectures use.
"""

import difflib
import re
import textwrap

from manim import (UL, Code, Create, Wait, FadeIn, FadeOut, Rectangle, ReplacementTransform, SurroundingRectangle, Transform,
                   VGroup, Animation, Arrow, Line, RIGHT)
import numpy as np

from lectern.settings import BOTTOM
from lectern.theme import T

__all__ = ["code", "register_painter", "glyphs", "line_of", "line", "lines", "span", "piece", "line_boxes", "CodeMixin",
           "CodeHighlighter"]

_PAINTERS = {}


def register_painter(lang, paint, pygments_lang="text"):
    """Color code in language `lang` with `paint(c, i, text)`, called for each source
    line i. Pygments lexes it as `pygments_lang` first ("text" means no colors)."""
    _PAINTERS[lang] = (paint, pygments_lang)


def background_kwargs():
    """Extra arguments for manim's Code: the theme's code background, if it has one.
    A light theme needs one, since manim's default dark gray would hide the code."""
    if not T.code_background:
        return {}
    return {"background_config": {"fill_color": T.code_background, "fill_opacity": 1, "stroke_color": T.muted,
                                  "stroke_width": 1, "buff": 0.3, "corner_radius": 0.2}}


def code(src, lang="java", font_size=24):
    """A code block from a source string. Leading indentation common to every line is
    removed, so you can indent the string to match your Python.

    The result is a manim `Code`, plus: `.src` (list of source lines), `.lang`,
    `.fs` (font size), and `.hl_box` (the current highlight, if any)."""
    src = textwrap.dedent(src).strip("\n")
    pygments_lang = _PAINTERS[lang][1] if lang in _PAINTERS else lang
    c = Code(code_string=src, language=pygments_lang, formatter_style=T.code_style,
             add_line_numbers=False, background="rectangle",
             paragraph_config={"font_size": font_size, "font": T.mono_font}, **background_kwargs())
    c.src = src.split("\n")
    c.lang = lang
    c.fs = font_size
    c.hl_box = None
    _paint(c)
    return c


def glyphs(c, line, start, stop):
    """The glyphs for source columns [start, stop) of 0-indexed `line`.

    manim's Code drops whitespace from each line's glyphs, so a column in the source
    has to be converted to a count of non-space characters before it can index them."""
    text = c.src[line]
    a = sum(1 for ch in text[:start] if not ch.isspace())
    b = sum(1 for ch in text[:stop] if not ch.isspace())
    return c.code_lines[line][a:b]


def _paint(c):
    for i, text in enumerate(c.src):
        if not text.strip():
            continue
        if text.lstrip().startswith("//:"):
            c.code_lines[i].set_color(T.code_text)
            glyphs(c, i, 0, text.index("//:") + 3).set_color(T.code_comment)
        elif c.lang in _PAINTERS:
            _PAINTERS[c.lang][0](c, i, text)
        for m in re.finditer(r"⟦[^⟧]*⟧", text):
            glyphs(c, i, m.start(), m.end()).set_color(T.bad)


def line_of(c, key, occ=0):
    """0-indexed line number. `key` is a 1-indexed line number, or text on that line
    (the `occ`th line containing it)."""
    if isinstance(key, int):
        return key - 1
    hits = [i for i, l in enumerate(c.src) if key in l]
    if not hits:
        raise KeyError(f"{key!r} isn't in the code:\n" + "\n".join(c.src))
    return hits[occ]


def line(c, key, occ=0):
    """The glyphs of one line (see `line_of` for `key`)."""
    return c.code_lines[line_of(c, key, occ)]


def lines(c, a, b, occ=0):
    """The glyphs of lines a through b, inclusive, skipping blank lines."""
    i, j = line_of(c, a, occ), line_of(c, b, occ)
    return VGroup(*[c.code_lines[k] for k in range(i, j + 1) if len(c.code_lines[k])])


def span(c, text, occ=0):
    """The glyphs of the `occ`th occurrence of `text` anywhere in the code."""
    n = 0
    for i, l in enumerate(c.src):
        start = -1
        while True:
            start = l.find(text, start + 1)
            if start < 0:
                break
            if n == occ:
                return glyphs(c, i, start, start + len(text))
            n += 1
    raise KeyError(f"{text!r} (occurrence {occ}) isn't in the code")


def piece(c, key, text, occ=0):
    """The glyphs of `text` on line `key`, e.g. the 7 in `li $t0,7`."""
    i = line_of(c, key, occ)
    col = c.src[i].index(text)
    return glyphs(c, i, col, col + len(text))


def highlight(c, target, color=None):
    """Animation: move `c`'s highlight (a filled background) behind `target`. The
    background stays inside its own line, however small the code has been scaled,
    so it can't cut into the lines around it."""
    color = color or T.focus
    pad_y = 0.06
    full = [(i, l) for i, l in enumerate(c.code_lines) if len(l.get_all_points())]  # blank lines have no points
    if len(full) > 1:
        (i0, l0), (i1, l1) = full[0], full[1]
        pitch = abs(l0.get_y() - l1.get_y()) / (i1 - i0)
        line_h = max(l.height for _, l in full)
        pad_y = max(0.0, min(0.06, (pitch - line_h) / 2))
    rect = Rectangle(width=target.width + 0.12, height=target.height + 2 * pad_y, stroke_color=color, stroke_width=1.5,
                     fill_color=color, fill_opacity=0.28).move_to(target)
    if c.hl_box is None:
        c.hl_box = rect
        return Create(rect)
    return Transform(c.hl_box, rect)


def line_boxes(c, spans, color=None, buff=0.06):
    """Outlines around several separate lines of a Code mobject (any Code, including
    one from a file). `spans` items are 1-indexed line numbers or (first, last) pairs;
    each item gets its own outline."""
    boxes = VGroup()
    for item in spans:
        a, b = item if isinstance(item, tuple) else (item, item)
        # WORKAROUND(manim 0.20): leave out blank lines; see CodeHighlighter.set_lines.
        picked = VGroup(*[l for l in c.code_lines[a - 1:b] if l.has_points() or l.submobjects])
        boxes.add(SurroundingRectangle(picked, color=color or T.focus, buff=buff))
    return boxes


class CodeMixin:
    """The code methods of SlideScene. `c` is always a block made by `code()`."""

    def code(self, src, lang="java", font_size=24):
        return code(src, lang, font_size)

    def plain(self, src, font_size=20):
        """A code block with no syntax coloring."""
        return code(src, lang="text", font_size=font_size)

    # Lookups, as methods so lectures can write self.line(c, 3).
    def line_of(self, c, key, occ=0):
        return line_of(c, key, occ)

    def line(self, c, key, occ=0):
        return line(c, key, occ)

    def lines(self, c, a, b, occ=0):
        return lines(c, a, b, occ)

    def span(self, c, text, occ=0):
        return span(c, text, occ)

    def piece(self, c, key, text, occ=0):
        return piece(c, key, text, occ)

    # Highlighting. hla() returns an animation; the others play it.
    def hl_to(self, c, target, color=None):
        return highlight(c, target, color)

    def hla(self, c, key, color=None, occ=0):
        """Animation: move the highlight to a whole line."""
        return highlight(c, line(c, key, occ), color)

    def hl(self, c, key, color=None, occ=0, rt=0.35):
        """Highlight one line. STYLE.md: one line at a time, never a bare brace."""
        self.play(self.hla(c, key, color, occ), run_time=rt)

    def hlr(self, c, a, b, color=None, rt=0.35):
        """Highlight a run of lines (one statement that wraps)."""
        self.play(highlight(c, lines(c, a, b), color), run_time=rt)

    def hls(self, c, text, color=None, occ=0, rt=0.35):
        """Highlight just `text`, e.g. the increment of a for loop."""
        self.play(highlight(c, span(c, text, occ), color), run_time=rt)

    def unhl(self, c, rt=0.3):
        if c.hl_box is not None:
            box, c.hl_box = c.hl_box, None
            self.play(FadeOut(box), run_time=rt)

    def mark(self, c, *texts, color=None, rt=0.35):
        """Outline each piece of text, in addition to the highlight. Returns the
        outlines, to hide later."""
        boxes = VGroup(*[SurroundingRectangle(span(c, t), color=color or T.focus, buff=0.04) for t in texts])
        self.play(Create(boxes), run_time=rt)
        return boxes

    def mark_lines(self, c, spans, color=None):
        """Animation: outline several separate lines at once (see `line_boxes`), replacing
        the previous mark_lines outlines. For two places in the code that go together,
        like a call and the function it calls."""
        boxes = line_boxes(c, spans, color)
        old, self._line_marks = getattr(self, "_line_marks", None), boxes
        return Create(boxes) if old is None else ReplacementTransform(old, boxes)

    def unmark_lines(self):
        """Animation: remove the mark_lines outlines."""
        old, self._line_marks = getattr(self, "_line_marks", None), None
        return FadeOut(old) if old is not None else Wait(0.01)

    def gutter_arrow(self, c, a, b, color=None, side=RIGHT, out=0.45, occ_a=0, occ_b=0):
        """A jump from line `a` to line `b`, drawn outside of the code box so it never
        crosses the code."""
        color = color or T.focus
        edge = c.get_right()[0] if side is RIGHT else c.get_left()[0]
        sign = 1 if side is RIGHT else -1
        y0, y1 = line(c, a, occ_a).get_y(), line(c, b, occ_b).get_y()
        p0, p1 = np.array([edge, y0, 0]), np.array([edge, y1, 0])
        pts = [p0, p0 + RIGHT * sign * out, p1 + RIGHT * sign * out, p1]
        return VGroup(Line(pts[0], pts[1], color=color, stroke_width=3), Line(pts[1], pts[2], color=color, stroke_width=3),
                      Arrow(pts[2], pts[3], buff=0, color=color, stroke_width=3, tip_length=0.16,
                            max_tip_length_to_length_ratio=0.5))

    def morph(self, old, new_src, rt=0.8, lang=None, keep_top_left=True, max_right=None):
        """Rewrite the code. Lines that didn't change move to their new places; the
        others fade out and in. STYLE.md: only the part that changes should change.
        `max_right`: shrink the new code (from its top left) so it ends before this x."""
        new = code(new_src, lang=lang or old.lang, font_size=old.fs)
        fresh = code("\n".join(old.src), lang=old.lang, font_size=old.fs)
        new.scale(old.width / fresh.width)  # the same scale `old` has been given
        new.move_to(old.get_corner(UL) - new.get_corner(UL) + new.get_center())
        if new.get_bottom()[1] < BOTTOM:
            corner = new.get_corner(UL)
            new.scale((new.get_top()[1] - BOTTOM) / new.height, about_point=corner)
        if max_right is not None and new.get_right()[0] > max_right:
            corner = new.get_corner(UL)
            new.scale((max_right - corner[0]) / new.width, about_point=corner)
        a, b = old.src, new.src
        sm = difflib.SequenceMatcher(None, [x.strip() for x in a], [x.strip() for x in b], autojunk=False)
        anims = [ReplacementTransform(old[0], new[0])]  # the background
        if old.hl_box is not None:
            anims.append(FadeOut(old.hl_box))
            old.hl_box = None
        for op, i0, i1, j0, j1 in sm.get_opcodes():
            if op == "equal":
                for i, j in zip(range(i0, i1), range(j0, j1)):
                    if len(old.code_lines[i]) and len(new.code_lines[j]):
                        anims.append(ReplacementTransform(old.code_lines[i], new.code_lines[j]))
            else:
                for i in range(i0, i1):
                    if len(old.code_lines[i]):
                        anims.append(FadeOut(old.code_lines[i]))
                for j in range(j0, j1):
                    if len(new.code_lines[j]):
                        anims.append(FadeIn(new.code_lines[j]))
        self.play(*anims, run_time=rt)
        self.remove(old)
        self.add(new)
        return new


class CodeHighlighter:
    """An outline that moves from line to line of a `Code` built from a file.

        c = self.code_block("code/bubble.c")
        h = CodeHighlighter(c, "code/bubble.c")
        self.play(h.set_line(3))

    Each method returns an animation: `Create` the first time, then `Transform`.
    With `path`, `set_substring` works, and a line that's just `{` or `}` clears the
    outline instead of boxing the brace (STYLE.md: never highlight a bare brace)."""

    def __init__(self, code, path=None, default_color=None):
        self.code = code
        self.path = path
        self.rect = None
        self.default_color = default_color

    def _color(self, color):
        return color or self.default_color or T.focus

    def _source_line(self, line_number):
        if self.path is None:
            return None
        with open(self.path) as f:
            src = f.read().split("\n")
        return src[line_number - 1] if 1 <= line_number <= len(src) else None

    def _is_brace_only(self, line_number):
        text = self._source_line(line_number)
        return text is not None and text.strip() in ("{", "}")

    def _code_lines(self):
        return getattr(self.code, "code_lines", None) or getattr(self.code, "lines", None)

    def _line(self, line_number):
        code_lines = self._code_lines()
        if code_lines is not None:
            return code_lines[line_number - 1] if 1 <= line_number <= len(code_lines) else None
        if hasattr(self.code, "get_line"):
            return self.code.get_line(line_number)
        subs = self.code.submobjects
        return subs[line_number - 1] if 1 <= line_number <= len(subs) else None

    def _animate_to(self, new_rect) -> Animation:
        if self.rect is None:
            self.rect = new_rect
            return Create(self.rect)
        return Transform(self.rect, new_rect)

    def _hide(self) -> Animation:
        if self.rect is None:
            return FadeOut(VGroup())
        rect, self.rect = self.rect, None
        return FadeOut(rect)

    def clear(self) -> Animation:
        """Remove the outline, e.g. when control returns from the highlighted function."""
        return self._hide()

    def set_line(self, line_number, color=None, buff=0.1) -> Animation:
        if self._is_brace_only(line_number):
            return self._hide()
        target = self._line(line_number)
        if target is None:
            raise ValueError(f"Cannot locate line {line_number} in the Code object.")
        return self._animate_to(SurroundingRectangle(target, color=self._color(color), buff=buff))

    def set_lines(self, start_line, end_line, color=None, buff=0.1) -> Animation:
        """One outline around lines start_line..end_line (1-indexed, inclusive)."""
        if start_line == end_line and self._is_brace_only(start_line):
            return self._hide()
        code_lines = self._code_lines()
        if code_lines is None:
            raise ValueError("Code object has no per-line submobjects to span.")
        # WORKAROUND(manim 0.20): a blank line is an empty VGroup, and manim's bounding
        # box of a group counts an empty member as the point (0, 0, 0), which stretches
        # the outline. Leave blank lines out before measuring.
        picked = VGroup(*[l for l in code_lines[start_line - 1:end_line] if l.has_points() or l.submobjects])
        return self._animate_to(SurroundingRectangle(picked, color=self._color(color), buff=buff))

    def set_substring(self, line_number, substring, color=None, buff=0.05, occurrence=0) -> Animation:
        """Outline only `substring` on `line_number`. Needs `path`."""
        if self.path is None:
            raise ValueError("CodeHighlighter needs `path` to locate a substring.")
        line_text = self._source_line(line_number)
        idx = -1
        for _ in range(occurrence + 1):
            idx = line_text.index(substring, idx + 1)
        start = sum(1 for ch in line_text[:idx] if not ch.isspace())
        length = sum(1 for ch in substring if not ch.isspace())
        target = self._code_lines()[line_number - 1][start:start + length]
        return self._animate_to(SurroundingRectangle(target, color=self._color(color), buff=buff))
