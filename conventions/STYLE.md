# House style

These are taste, not syntax. `SCRIPT_CONVENTIONS.md` says how to *write* a script.
This file says what a good slide *looks like*. Agents translating a script should
follow both, and check the finished lecture against this list.

Change anything here to suit your course. A course can also keep its own additions
in its own conventions file (see `templates/course/`).

## Colors mean something

Each color is a role in the theme (`lectern.theme`), so the same lecture can be
rendered in any theme, including the colorblind-safe ones.

| role      | default (dark theme) | meaning                                                   |
|-----------|----------------------|-----------------------------------------------------------|
| `focus`   | yellow               | what we're looking at right now                           |
| `good`    | green                | matched, found, correct, reachable                        |
| `bad`     | red                  | error, conflict, clobbered                                |
| `current` | blue                 | the current position: a cursor, `$sp`, the current vertex |
| `muted`   | gray                 | dead: garbage, popped values, things we've thrown away    |

* Use the role, never the color: `T.focus`, not `YELLOW`.
* **Never rely on color alone.** About 1 in 12 men has some color blindness. Pair
  good/bad with a mark (✓ / ✗, a strike-through, a label) so the slide still reads
  in grayscale.

## Things move

* If a value goes from one place to another, animate that value moving. Registers,
  memory cells, and stack cells take `src=`: a copy of the source moves into the cell
  and becomes the new value, while the old value fades (`lectern.anim.arrive`).
* A computed value moves in from all of its operands, which merge.
* A value that's in flight with nowhere on screen to sit (popped into a register
  that isn't drawn) is held with `self.carry()` until it lands.
* The only in-place changes are starting states, hypotheticals ("what if this were
  null?"), and a variable updating itself (`i++`).
* Don't transform one number into another, and don't let a new structure pop into
  existence.
* Equations and code that change: only the part that changes should change.
  Everything else keeps its position and its identity (see "Algebraic
  transformations" in `SCRIPT_CONVENTIONS.md`, and `self.morph` for code).
* Anything that fades out stays faded out through the slide transition.

## Highlighting

* Code: one line at a time, and never just a curly brace.
* In a loop, highlight the whole header the first time around, and only the
  increment after that.
* An array or memory cell is highlighted by changing its background color.

## Code

* Braces go on their own line, below the `if`, loop, method, or class (Allman style).
* A `for` header stays on one line.

## Math

* Big-O is written `\mathcal{O}\left( ... \right)`.

## Slides carry what the viewer needs to see

* About 35 words of prose per slide at most. Narration goes in `note:` lines, which
  appear in the presenter view, not on the slide.
* Nothing smaller than 20pt. If a reference (a grammar, a rule set, an instruction
  table) won't fit, show the part being discussed and tag the slide with the handout
  that has all of it (`self.handout("Grammar.pdf")`).
* Pause often: one idea per click.
* Every lecture ends with a short Recap slide.
* Aim for about 10 minutes per lecture video.

## No practice slides

* No "check yourself" or "try this at home" slides. (This course practices in class.
  Delete this rule if yours doesn't.)
