# MIPS conventions

Script directives for MIPS assembly. `MipsMixin` and `Regs` are in `__init__.py`.
Memory and stack diagrams are in the memory extra.

## Code

`mips code` followed by the assembly. Labels, instructions, registers, and comments
are colored (theme roles `code_label`, `code_keyword`, `code_variable`,
`code_comment`).

## Registers

A small column of boxes off to one side, labeled `$t0`, `$t1`, …. In code:
`Regs(["$t0", "$t1"])`, and `regs.set("$t0", "7", src=...)` to load one.

## Running assembly

"Run the code" means: code on the left, stack and registers on the right, highlight
one instruction at a time, and show that instruction's effect before moving on.
Pause after the first few instructions, then run the rest at a steady pace.

## Code generation rules

A rule is a math heading over assembly:

```
text: \llbracket e_1 + e_2 \rrbracket =
mips code
⟦e1⟧
⟦e2⟧
pop $t2
```

Inside the assembly, `⟦e1⟧` means "the code for e_1", drawn in the `bad` color.
Anything else in that color in a rule is filled in by the compiler rather than typed
literally. In code: `self.rule("e_1 + e_2", SRC)`.
