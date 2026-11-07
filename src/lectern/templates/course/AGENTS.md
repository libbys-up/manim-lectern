# AGENTS.md

Instructions for agents (and people) making lecture videos in this folder with
[manim-lectern](https://github.com/libbys-up/manim-lectern).

## The workflow

1. The author writes a script: `scripts/<lecture>.md`, in the markup from lectern's
   `conventions/SCRIPT_CONVENTIONS.md`, plus this course's additions in
   `COURSE_CONVENTIONS.md`.
2. You translate it into `lectures/<lecture>.py`: one `SlideScene` subclass named the
   CamelCase of the file name (`lr_tables.py` → `LrTables`).
3. Render it, check it (below), and fix what you find.
4. The author watches it and writes fixes. Apply them to the lecture, and to the
   script if the fix changes what the script says.

## Before translating, read

- lectern's `conventions/SCRIPT_CONVENTIONS.md`: what each piece of markup means.
- lectern's `conventions/STYLE.md`: how slides should behave. Check every lecture
  against it before calling it done.
- `COURSE_CONVENTIONS.md` here. Where it disagrees with lectern's files, it wins.
- The docstrings of what you use: `lectern/slide.py` for `SlideScene`, the module of
  each structure, and the `CONVENTIONS.md` of each extra.

`lectern where` prints where all of these files are.

Use what lectern provides before writing your own. If you find yourself drawing a
structure by hand that lectern almost has, say so: it may belong in the library.

## Writing a lecture

```python
from manim import *
from lectern import *


class LinearSearch(SlideScene):
    def construct(self):
        a = Array([3, 7, 2, 9, 4])
        self.page("Linear Search",
            "* Walk through the array and check each value",
            "* Stop as soon as we find a match",
            P,
            C(a),
            P,
            lambda: self.play(a.highlight_cell(0)),
            N("Seven isn't three, so we move on."),
        )
```

- Colors are theme roles: `T.focus`, `T.good`, `T.bad`, `T.current`, `T.muted`,
  `T.text`. Never `YELLOW` or a hex string, or the lecture can't be re-themed.
- Structure methods return animations; pass them to `self.play(...)` or `self.go(...)`.
- Lay out with `page()`/`panes()`/`more()`. They fit everything to the screen before
  anything is revealed, so nothing moves or runs off the edge.

## Commands

Run from this folder:

```
manim-slides render -ql lectures/<lecture>.py <Scene>    # -ql low quality, -qm, -qh
manim-slides present <Scene>
```

Check layout while rendering (an approximate report: off-screen, overlapping, and
crossed-out text):

```
LECTERN_BOUNDS=/tmp/issues.txt manim-slides render -ql lectures/<lecture>.py <Scene>
```

Re-render in another theme without changing code:

```
LECTERN_THEME=dark-colorblind manim-slides render -qm lectures/<lecture>.py <Scene>
```

Rendering several lectures at once can fail with "latex failed" because they share the
TeX cache in `media/`. That's not a real error: render that lecture again by itself.

## Folder layout

```
scripts/      one script per lecture
lectures/     one lecture file per script
code/         source files shown in lectures (optional)
graphs/       .gr graph files (optional)
images/       images (optional)
lectern.toml  theme choice and custom themes (optional)
```

## Working rules

- Look at what's in a folder before creating or cleaning up files there.
- Never delete a file you didn't create in this session without asking.
- Don't change a lecture's script to make the translation easier. If the script
  asks for something hard, do it or ask.
