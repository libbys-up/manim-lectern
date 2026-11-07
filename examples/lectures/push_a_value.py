"""Translated from scripts/push_a_value.md. Uses the assembly/mips and memory extras.

    manim-slides render -ql lectures/push_a_value.py PushAValue
"""

from manim import *
from lectern import *
from lectern.extras.assembly.mips import MipsMixin, Regs
from lectern.extras.memory import StackView

SRC = """
li    $t0, 7
addiu $sp, $sp, -4
sw    $t0, 0($sp)
"""


class PushAValue(MipsMixin, SlideScene):
    def construct(self):
        c = self.mips(SRC, font_size=28)
        regs = Regs(["$t0"])
        self.panes("Pushing a value", left=[c, "", regs], right=[])

        # The first cell pushed is at 0x7FFC: $sp starts at 0x8000 and moves down 4.
        stack = StackView(top=(3.5, 1.5), addrs=True, start=0x7FFC)
        self.show(*stack.start_mobs())
        self.pause()

        self.hl(c, "li")
        # STYLE.md: values move. The 7 travels from the instruction into $t0.
        self.play(regs.set("$t0", "7", src=self.piece(c, "li", "7")))
        self.pause()

        self.hl(c, "addiu")
        self.go(stack.push(" "))
        self.pause()

        self.hl(c, "sw")
        self.go(stack.set_val(0, "7", src=regs.vals["$t0"]))
        self.note("The value is copied. $t0 still holds 7.")
        self.pause()
