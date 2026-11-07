# Memory conventions

Script directives for memory, stack, and object-layout diagrams. `Mem`, `StackView`,
and `Pointer` are in `__init__.py`.

## Memory and stack diagrams

```
[memory: this @ 24($sp), tag @ 20($sp), x @ 16($sp), y @ 12($sp), RA @ ($sp)]
```

A column of same-width cells listed top to bottom, with the label after each `@` on
the left of its cell in code font.

* **High addresses are at the top of the screen**, so the stack grows down the
  screen, and the most recently pushed item is the bottom cell.
* Addresses or offsets go on the left of the cells.
* A cell with no `@` has no label.
* A register that points into memory (`$sp`) is an arrow in the `current` color,
  from the right. When it moves, offsets relative to it update.
* Popping a cell fades it to `muted`, then removes it. The memory is still there;
  we just don't care about it anymore.
* Bookkeeping cells (GC tags) are drawn smaller and dim, so they read as bookkeeping
  rather than data. Set `Mem.dim_values` / `StackView.dim_values` for your
  language's names for them.

The same diagram is used for objects, with a pointer into the middle of the column.

## Values move

Every value that changes takes `src=`: the thing on screen it came from, whose copy
moves into the cell (STYLE.md "Things move"). In code: `m.put(i, "7", src=...)`,
`stack.push("7", src=...)`, `stack.set_val(i, "7", src=...)`.
