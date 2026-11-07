"""Programming language semantics: inference rules and semantic brackets.

    from lectern.extras.semantics import Rule

    r = Rule([r"\\Gamma \\vdash e_1 : int", r"\\Gamma \\vdash e_2 : int"],
             r"\\Gamma \\vdash e_1 + e_2 : int", name=r"\\textsc{Add}")

Premises are LaTeX strings or other Rules, so a whole derivation is one Rule.
Importing this module adds the stmaryrd package, for \\llbracket and \\rrbracket
(denotational semantics, code generation rules).

Conventions: CONVENTIONS.md in this folder.
"""

from manim import DOWN, LEFT, RIGHT, UP, Line, MathTex, VGroup

from lectern.tex import use_packages
from lectern.theme import T

__all__ = ["Rule"]

use_packages("stmaryrd")


class Rule(VGroup):
    """`[rule: a ;; b => c]` in a script: premises over a bar, conclusion under it,
    and an optional rule name to the right of the bar."""

    def __init__(self, prems, concl, font_size=36, name=None):
        super().__init__()
        self.prem = [p if isinstance(p, Rule) else MathTex(p, font_size=font_size, color=T.text) for p in prems]
        self.con = MathTex(concl, font_size=font_size, color=T.text)
        top = VGroup(*self.prem)
        if len(self.prem):
            top.arrange(RIGHT, buff=0.55, aligned_edge=DOWN)
        w = max(top.width if len(self.prem) else 0, self.con.width) + 0.15
        self.bar = Line(LEFT * w / 2, RIGHT * w / 2, stroke_width=2, color=T.text)
        if len(self.prem):
            top.next_to(self.bar, UP, buff=0.12)
        self.con.next_to(self.bar, DOWN, buff=0.12)
        self.add(top, self.bar, self.con)
        if name:
            self.name_ = MathTex(name, font_size=font_size * 0.7, color=T.text).next_to(self.bar, RIGHT, buff=0.1)
            self.add(self.name_)

    def heads(self):
        """The premises' own text: a premise that is a Rule contributes its conclusion."""
        return [p.con if isinstance(p, Rule) else p for p in self.prem]

    def text(self):
        """Every premise and conclusion that's text, for a highlight."""
        return VGroup(*self.heads(), self.con)

    def own(self):
        """This rule's bar and premises, without the sub-derivations above them."""
        return VGroup(self.bar, *self.heads())
