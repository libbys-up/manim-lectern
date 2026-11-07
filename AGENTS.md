# AGENTS.md: working on manim-lectern

This file is for agents (and people) changing the library. If you're writing
lectures *with* lectern, read `templates/course/AGENTS.md` instead. It's the file
that goes in a course folder.

## What this is

A Python library on top of [manim](https://www.manim.community/) and
[manim-slides](https://manim-slides.eertmans.be/) for animated lecture slides. Authors
write scripts in the markup in `conventions/SCRIPT_CONVENTIONS.md`; a person or an agent
translates each script into a `SlideScene`, using the helpers here.

## Layout

```
src/lectern/
  slide.py        SlideScene: slides, pauses, notes, page()/panes() layout, reveals
  text.py         inline markup, $math$ in prose, line breaking
  code.py         code blocks and highlighting
  table.py        tables
  boxes.py        definition boxes, terminal boxes, outlines
  anim.py         Arrive / arrive(): values that move (STYLE.md "Things move")
  theme.py        themes and the T roles; no color is named anywhere else
  bounds.py       the optional layout report (LECTERN_BOUNDS)
  settings.py     layout constants
  markers.py      P, N, C, H for page() lists
  tex.py          extra LaTeX packages
  structures/     data structures (each module's docstring shows its use)
  extras/<topic>/ topic extensions: parsing, assembly/mips, memory, semantics
conventions/      SCRIPT_CONVENTIONS.md (markup), STYLE.md (house style)
templates/course/ files `lectern init` would copy into a new course folder
examples/         scripts next to the lectures made from them
tools/            themeify.py: convert manim color names to theme roles
```

## Rules

1. **Core never imports from extras.** Extras may import core and each other.
2. **No color literals.** Use theme roles (`T.focus`, `T.text`, …). A function's
   default color is `color=None`, resolved inside with `color or T.focus`, because a
   default argument is evaluated once, before the theme is chosen. The exceptions
   are colors that are part of what's being shown (a DFS vertex named WHITE is
   white in every theme); comment those.
3. **Methods that change a structure return animations.** They don't play them, so
   callers can combine them in one `self.play(...)`.
4. **Draw from logical positions, not live coordinates.** Pointers and edges are
   computed from stored positions/indices, because a mobject can be mid-animation
   when a pointer needs to be redrawn to where it's going.
5. **Label every workaround** with a comment in this form, so they can all be found
   with `grep -rn WORKAROUND`:

   ```python
   # WORKAROUND(manim 0.20): <what goes wrong>. <why this avoids it>.
   ```

   Add new ones to the list in README.md.
6. **Every public function has a docstring** that says what it's for in lecture
   terms, with a short example when the call isn't obvious. Module docstrings start
   with a usage example.
7. **Prefer readable over clever.** Lecture authors and their agents read this code to
   learn what's available. Name things for what they mean on a slide.
8. **Don't change how existing lectures render** unless that's the point of the
   change. Check with the frame comparison below.

## Adding an extra

`src/lectern/extras/<topic>/` with:

- `__init__.py`: a mixin class for scene methods (`class FooMixin:`) and/or
  structures, with a module docstring showing a complete use.
- `CONVENTIONS.md`: any script directives and style rules the topic adds.
- An example in `examples/`.

Name the extra for the *topic*, not the course (`parsing`, not `compilers`), so
other courses that touch the topic find it.

## Checking a change

There's no unit test suite yet. The check is rendering:

```
cd examples && manim-slides render -ql <example>.py <Scene>
```

To make sure a change doesn't alter existing lectures, render them before and after
in two folders and compare the last frame of every slide:

```
python tools/compare_slides.py before/ after/ --save diffs/
```

Any difference should be one you meant. Also render the examples with
`LECTERN_THEME=light` and `LECTERN_THEME=dark-colorblind`, since a color that's fine
on black can disappear on white.

`LECTERN_BOUNDS=/tmp/issues.txt` during a render writes a report of text off screen,
overlapping, or crossed by lines. It's approximate: it misses things and flags some
things that look fine.
