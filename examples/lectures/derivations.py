"""Translated from scripts/derivations.md. Uses the parsing extra.

    manim-slides render -ql lectures/derivations.py Derivations
"""

from manim import *
from lectern import *
from lectern.extras.parsing import ParsingMixin


class Derivations(ParsingMixin, SlideScene):
    def construct(self):
        g = self.grammar(r"E \rightarrow E + T", r"E \rightarrow T", r"T \rightarrow id", numbered=True)
        self.page("A grammar",
            C(g),
            P,
            "* Each line is a *production*: the left side can be replaced by the right",
            "* `id` is a *terminal*; `E` and `T` are *nonterminals*",
        )

        g2 = self.grammar(r"E \rightarrow E + T", r"E \rightarrow T", r"T \rightarrow id", numbered=True)
        self.page("Deriving id + id", C(g2))
        # The production used at each step (0-based), and the sentential form after it.
        steps = [(None, "E"), (0, "E + T"), (1, "T + T"), (2, "id + T"), (2, "id + id")]
        self.expand(steps, g2, y=-1.8, font_size=48)
        self.note("We always expanded the leftmost nonterminal. That's a leftmost derivation.")

        t = LabelTree("E [E [T id]] + [T id]")
        self.page("The parse tree", C(t))
        self.pause()
        self.play(t.lit("+"))
        self.pause()
        self.more("* The tree records *which* production made each node, not the order we used them")
        self.pause()
