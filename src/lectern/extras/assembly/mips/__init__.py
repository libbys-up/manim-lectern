"""MIPS assembly: syntax coloring, registers, and code generation rules.

    from lectern import *
    from lectern.extras.assembly.mips import MipsMixin, Regs

    class Intro(MipsMixin, SlideScene):
        def construct(self):
            c = self.mips('''
                main:
                    li $t0, 7       # load 7
                    addu $t1, $t0, $t0
            ''')
            r = Regs(["$t0", "$t1"])
            self.panes("Registers", left=[c], right=[r])
            self.hl(c, "li")
            self.play(r.set("$t0", "7", src=self.piece(c, "li", "7")))

Importing this module registers "mips" as a code language (see lectern.code), so
`self.code(src, lang="mips")` colors labels, instructions, registers, and comments.
For memory and the stack, see lectern.extras.memory.

Conventions: CONVENTIONS.md in this folder.
"""

import re

from manim import DOWN, LEFT, RIGHT, MathTex, Rectangle, VGroup

from lectern.anim import arrive
from lectern.code import code, glyphs, register_painter
from lectern.text import mono
from lectern.theme import T
import lectern.extras.semantics  # noqa: F401  (rule() needs \llbracket from stmaryrd)

__all__ = ["MipsMixin", "Regs", "paint_mips"]


def paint_mips(c, i, text):
    """Color one line of MIPS: `# comments`, `labels:`, the instruction, `$registers`."""
    src, hash_at = text, text.find("#")
    if hash_at >= 0:
        glyphs(c, i, hash_at, len(text)).set_color(T.code_comment)
        src = text[:hash_at]
    stripped = src.strip()
    if not stripped:
        return
    start = len(src) - len(src.lstrip())
    if stripped.endswith(":"):
        glyphs(c, i, start, start + len(stripped)).set_color(T.code_label)
        return
    first = stripped.split()[0]
    glyphs(c, i, start, start + len(first)).set_color(T.code_keyword)
    for m in re.finditer(r"\$\w+", src):
        glyphs(c, i, m.start(), m.end()).set_color(T.code_variable)


register_painter("mips", paint_mips)


class Regs(VGroup):
    """A small column of named registers, empty to start. `notes`: {name: text}
    shown to the right of a register (what it's used for)."""

    def __init__(self, names, width=1.5, height=0.42, font_size=20, notes=None, direction=DOWN):
        super().__init__()
        self.boxes, self.vals = {}, {}
        notes = notes or {}
        self.font_size = font_size
        for name in names:
            box = Rectangle(width=width, height=height, stroke_width=2, color=T.text)
            lab = mono(name, font_size=font_size, color=T.label).next_to(box, LEFT, buff=0.12)
            val = mono(" ", font_size=font_size).move_to(box)
            row = VGroup(lab, box, val)
            if name in notes:
                row.add(mono(notes[name], font_size=font_size - 4, color=T.muted).next_to(box, RIGHT, buff=0.1))
            self.boxes[name], self.vals[name] = box, val
            self.add(row)
        self.arrange(direction, aligned_edge=RIGHT if not notes else LEFT, buff=0.1)

    def set(self, name, text, color=None, src=None):
        """Animation: register `name` gets `text`, carried from `src` if given."""
        new = mono(text, font_size=self.font_size, color=color or T.text)
        if new.width > self.boxes[name].width - 0.1:
            new.scale_to_fit_width(self.boxes[name].width - 0.1)
        new.move_to(self.boxes[name])
        return arrive(self.vals[name], new, src)


class MipsMixin:

    def mips(self, src, font_size=24):
        """A MIPS code block (see lectern.code for highlighting it)."""
        return code(src, lang="mips", font_size=font_size)

    def rule(self, head, src, font_size=22, head_size=34):
        """A code generation rule: ⟦head⟧ = over its assembly. `.c` is the code block.
        Write ⟦e⟧ inside `src` for a placeholder (drawn in the `bad` color)."""
        h = MathTex(rf"\llbracket {head} \rrbracket =", font_size=head_size, color=T.text)
        c = self.mips(src, font_size=font_size)
        g = VGroup(h, c).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        g.c = c
        return g
