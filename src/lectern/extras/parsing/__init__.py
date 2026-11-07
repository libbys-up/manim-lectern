"""Grammars, derivations, and scanning input: lexing and parsing lectures.

Mix `ParsingMixin` into your scene:

    from lectern import *
    from lectern.extras.parsing import ParsingMixin

    class Derivations(ParsingMixin, SlideScene):
        def construct(self):
            g = self.grammar(r"E \\to E + T", r"E \\to T", r"T \\to id", numbered=True)
            self.page("A derivation", C(g))
            self.expand([(None, "E"), (0, "E + T"), (1, "T + T"), (2, "id + T"), (2, "id + id")], g)

Related core pieces: `chars()`/`tokens()` rows (lectern.structures.row) for input
streams, and `LabelTree` for parse trees.

Conventions: CONVENTIONS.md in this folder.
"""

import difflib

from manim import DOWN, LEFT, RIGHT, UP, Create, FadeIn, FadeOut, MathTex, ReplacementTransform, Text, Transform, VGroup

from lectern.theme import T

__all__ = ["ParsingMixin"]


class ParsingMixin:

    def grammar(self, *prods, font_size=40, numbered=False):
        """Productions in math font, one per line. `g.prods[i]` is production i."""
        rows = VGroup()
        for i, p in enumerate(prods):
            body = MathTex(p, font_size=font_size, color=T.text)
            if numbered:
                body = VGroup(Text(f"{i + 1}.", font_size=font_size - 8, color=T.text), body).arrange(RIGHT, buff=0.2)
            rows.add(body)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        rows.prods = rows
        return rows

    def deriv(self, text, y=None, font_size=44, x=0.0):
        """A sentential form: space-separated math tokens, each its own mobject, so
        `rewrite` can move the ones that survive a step."""
        toks = text.split()
        parts = VGroup(*[MathTex(c, font_size=font_size, color=T.text) for c in toks])
        for p in parts:  # keep every token on one baseline
            base = MathTex("x", p.get_tex_string(), font_size=font_size)
            p.shift(UP * (base[1].get_center()[1] - base[0].get_bottom()[1] - p.get_center()[1]))
        x_pos = 0.0
        for p in parts:
            p.shift(RIGHT * (x_pos - p.get_left()[0]))
            x_pos = p.get_right()[0] + 0.14
        parts.toks = toks
        parts.move_to([x, parts.get_center()[1] if y is None else y, 0])
        return parts

    def rewrite(self, old, text, rt=0.6, extra=()):
        """Go to a new sentential form. Tokens that survive move; the rest fade."""
        new = self.deriv(text, y=old.get_center()[1], font_size=getattr(old, "fs", 44), x=old.get_center()[0])
        new.fs = getattr(old, "fs", 44)
        sm = difflib.SequenceMatcher(None, old.toks, new.toks, autojunk=False)
        anims = list(extra)
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op == "equal":
                for i, j in zip(range(a0, a1), range(b0, b1)):
                    anims.append(ReplacementTransform(old[i], new[j]))
            else:
                for i in range(a0, a1):
                    anims.append(FadeOut(old[i]))
                for j in range(b0, b1):
                    anims.append(FadeIn(new[j]))
        self.play(*anims, run_time=rt)
        self.remove(old, *old)
        self.add(new)
        return new

    def expand(self, steps, grammar, y=-1.2, font_size=44, pauses=3):
        """Walk a derivation. `steps` are (production index, text); the first step's
        index is ignored. The production used is boxed in `grammar` at each step,
        with a pause after each of the first `pauses` steps."""
        cur = self.deriv(steps[0][1], y=y, font_size=font_size)
        cur.fs = font_size
        self.show(cur)
        box = None
        for n, (prod, text) in enumerate(steps[1:]):
            new_box = self.surround(grammar[prod], T.focus, 0.05)
            self.play(Create(new_box) if box is None else Transform(box, new_box), run_time=0.3)
            box = box or new_box
            cur = self.rewrite(cur, text)
            if n < pauses:
                self.pause()
        self.hide(box)
        return cur

    def peek_at(self, row, i, ok, keep=False):
        """Lookahead: a dashed box pokes at cell i of a Row, and turns good or bad.
        Nothing is consumed."""
        box = row.peek(i)
        self.play(Create(box), run_time=0.25)
        self.play(box.animate.set_color(T.good if ok else T.bad), run_time=0.2)
        if not keep:
            self.play(FadeOut(box), run_time=0.2)
        return box

    def grow_bracket(self, row, i, j, label=None, color=None, old=None, direction=DOWN):
        """A brace under cells i..j of a Row (a lexeme so far). Pass the previous
        brace as `old` to stretch it instead of drawing a new one."""
        new = row.bracket(i, j, label, color, direction)
        if old is None:
            self.play(FadeIn(new), run_time=0.25)
            return new
        self.play(Transform(old, new), run_time=0.2)
        return old
