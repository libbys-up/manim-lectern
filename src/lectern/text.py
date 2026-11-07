"""Text: the inline markup from SCRIPT_CONVENTIONS.md, turned into manim mobjects.

    **bold**      bold
    *emphasis*    italic, in the theme's focus color
    `code`        monospace; nothing inside it is markup
    ``a`b``       code that contains a backtick
    $x^2$         LaTeX math, on the same baseline as the prose around it
    \\*           a literal asterisk

These are plain functions so structures can use them. `SlideScene` has methods
with the same names that call them.
"""

import re

from manim import DOWN, LEFT, RIGHT, UP, MarkupText, MathTex, Rectangle, Text, VGroup

from lectern.settings import PANE_FONT_SIZE
from lectern.theme import T

__all__ = ["mono", "markup", "styled", "mixed", "split_lines", "txt", "item", "BULLETS", "ordinal"]

BULLETS = ["•", "◦", "▪"]  # markers for list depth 0, 1, 2+


def _roman(n):
    out = ""
    for value, symbol in [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]:
        while n >= value:
            out += symbol
            n -= value
    return out


def ordinal(depth, n):
    """The marker for item n of a numbered list at `depth`: 1. then a. then i."""
    if depth == 0:
        return f"{n}."
    if depth == 1:
        return f"{chr(ord('a') + n - 1)}."
    return f"{_roman(n)}."

# Stands in for a backtick inside of a code span while the rest of the markup is
# processed. Any character that never appears in lecture text works.
_BACKTICK = "\x01"


def mono(text, font_size=24, color=None):
    """Monospace text, with no markup."""
    return Text(str(text), font=T.mono_font, font_size=font_size, color=color or T.text)


def _normalize(text):
    """``x`` is code that may contain a backtick, like `` `+``. A literal \\" is just a quote."""
    text = text.replace('\\"', '"')
    return re.sub(r"``\s*(.+?)``", lambda m: "`" + m.group(1).replace("`", _BACKTICK) + "`", text)


def _escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def markup(text):
    """Script markup -> Pango markup. Nothing inside of `code` is markup, but bold and
    emphasis can go around it."""
    codes = []

    def stash(m):
        body = _escape(m.group(0)[1:-1]).replace(_BACKTICK, "`")
        codes.append(f'<span font_family="{T.mono_font}">{body}</span>')
        return f"\x00{len(codes) - 1}\x00"

    s = _escape(re.sub(r"`[^`]+`", stash, _normalize(text)))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\\)\*(.+?)(?<!\\)\*", rf'<span foreground="{T.focus}"><i>\1</i></span>', s)
    s = s.replace("\\*", "*")
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)


def _font_kwargs():
    return {"font": T.body_font} if T.body_font else {}


def styled(text, font_size=PANE_FONT_SIZE, color=None):
    """One line of prose with inline markup. Uses `mixed` if there's any $math$."""
    color = color or T.text
    text = _normalize(text)
    pieces = re.split(r"(`[^`]+`)", text)
    if any("$" in p for p in pieces if not p.startswith("`")):
        return mixed(text, font_size=font_size, color=color)
    return MarkupText(markup(text), font_size=font_size, color=color, **_font_kwargs())


def mixed(text, font_size=PANE_FONT_SIZE, color=None):
    """Prose and $math$ on one baseline. `$` inside of `code` isn't math.

    Each piece is typeset behind a throwaway "x" whose bottom marks the baseline,
    so pieces with and without descenders line up."""
    color = color or T.text
    space = 0.15 * font_size / 30
    lines = text.split("\n")
    if len(lines) > 1:  # one row per line, keeping each line's leading spaces as an indent
        rows = VGroup(*[mixed(line, font_size, color) for line in lines])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.12 * font_size / 30)
        for row, line in zip(rows, lines):
            row.shift(RIGHT * space * (len(line) - len(line.lstrip(" "))))
        return rows
    codes = []

    def stash(m):
        codes.append(m.group(0))
        return f"\x00{len(codes) - 1}\x00"

    hidden = re.sub(r"`[^`]+`", stash, text)
    back = lambda s: re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)
    row = VGroup()
    x = 0.0
    prev_space = False
    for i, piece in enumerate(re.split(r"\$(.+?)\$", hidden)):
        is_math = i % 2 == 1
        if not is_math and not piece.strip():
            prev_space = prev_space or bool(piece)
            continue
        if is_math:
            mob = MathTex("x", piece, font_size=font_size * 1.25, color=color)
            base, body = mob[0], mob[1]
        else:
            mob = MarkupText("x" + markup(back(piece.strip())), font_size=font_size, color=color, **_font_kwargs())
            base, body = mob[0], VGroup(*mob[1:])
        body.shift(DOWN * base.get_bottom()[1])
        gap = space if (prev_space or (not is_math and piece[:1].isspace())) else 0.05
        if len(row):
            x += gap
        body.shift(RIGHT * (x - body.get_left()[0]))
        x = body.get_right()[0]
        row.add(body)
        prev_space = not is_math and piece[-1:].isspace()
    return row


# ---------------------------------------------------------------- line breaking

_NO_BREAK_AFTER = {"e.g.", "i.e.", "vs.", "etc.,", "e.g.,", "i.e.,", "Dr.", "Mr.", "Ms."}


def _balanced(s):
    """True if `s` doesn't end inside of `code`, $math$, or *emphasis*."""
    no_code = re.sub(r"`[^`]*`", "", s)
    if s.count("`") % 2:
        return False
    if no_code.count("$") % 2:
        return False
    return no_code.replace("\\*", "").count("*") % 2 == 0


def _break_cost(word):
    """How bad it is to end a line after `word`: 0 after a sentence or clause,
    1 after a comma, 3 anywhere else."""
    if word in _NO_BREAK_AFTER:
        return 3
    end = re.sub(r"[`*$)\]\"'’”]+$", "", word)[-1:]
    if end and end in ".?!;:":
        return 0
    if end == "," or word.endswith(("—", "–", "--")):
        return 1
    return 3


def _break_words(words, limit, visible):
    """Fill lines up to `limit` visible characters, in as few lines as greedy filling
    would use, but prefer to break after punctuation. A line that ends at punctuation
    should still be at least a quarter full, so a lone "Yes," doesn't sit on its own line."""
    n = len(words)
    width = lambda i, j: visible(" ".join(words[i:j]))
    INF = (float("inf"),)
    best = [INF] * (n + 1)  # best[i]: cost of laying out words[i:]
    nxt = [n] * (n + 1)
    best[n] = (0, 0, 0)
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n + 1):
            w = width(i, j)
            if w > limit and j > i + 1:
                break
            rest = best[j]
            if rest == INF:
                continue
            if j == n:
                cost = (1, 0, 0)
            else:
                c = _break_cost(words[j - 1])
                if c < 3 and w < limit / 4:
                    c = 3
                cost = (1, c, (limit - w) ** 2)
            total = tuple(a + b for a, b in zip(cost, rest))
            if total < best[i]:
                best[i], nxt[i] = total, j
    lines, i = [], 0
    while i < n:
        lines.append(" ".join(words[i:nxt[i]]))
        i = nxt[i]
    return lines


def split_lines(text, font_size, max_w):
    """Break prose into lines no wider than `max_w`, at spaces outside of markup, so
    nothing has to shrink."""
    text = _normalize(text)
    mob = styled(text, font_size=font_size)
    if mob.width <= max_w:
        return [text]
    words, pos = [], 0
    for m in re.finditer(r"\s+", text):
        if _balanced(text[:m.start()]):
            words.append(text[pos:m.start()])
            pos = m.end()
    words.append(text[pos:])
    visible = lambda s: len(re.sub(r"[`*]", "", s))
    limit = max(10, int(visible(text) * max_w / mob.width * 0.97))
    return _break_words(words, limit, visible)


def txt(text, font_size=PANE_FONT_SIZE, color=None, max_w=12.8):
    """A paragraph, wrapped to `max_w`. A line starting with "* " is a bullet (see `item`)."""
    if re.match(r"^\s*\*\s", text):
        rows = item(text, font_size, max_w)
        return rows.set_color(color) if color else rows
    lines = split_lines(text, font_size, max_w)
    rows = VGroup(*[styled(l, font_size=font_size, color=color) for l in lines])
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    if rows.width > max_w:
        rows.scale_to_fit_width(max_w)
    return rows


def item(s, font_size, max_w):
    """One entry of a page() list. "* text" is a bullet and "1. text" is numbered;
    two leading spaces per level of nesting. Anything else is a paragraph."""
    m = re.match(r"^(\s*)([*]|\d+\.)\s+(.*)$", s, re.S)
    if not m:
        return txt(s, font_size, max_w=max_w)
    depth = len(m.group(1)) // 2
    marker = m.group(2)
    if marker == "*":
        marker = BULLETS[min(depth, len(BULLETS) - 1)]
    indent = 0.45 * depth
    size = font_size if depth == 0 else font_size - 2
    lines = split_lines(f"{marker} {m.group(3)}", size, max_w - indent)
    rows = VGroup(*[styled(l, font_size=size) for l in lines])
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    for r in rows[1:]:  # hanging indent for wrapped lines
        r.shift(RIGHT * 0.3)
    rows.shift(RIGHT * indent)
    # An invisible spacer keeps the indent when a column aligns left edges.
    pad = Rectangle(width=indent + 0.001, height=0.001, stroke_opacity=0, fill_opacity=0)
    pad.next_to(rows, LEFT, buff=0, aligned_edge=UP)
    return VGroup(pad, rows)

