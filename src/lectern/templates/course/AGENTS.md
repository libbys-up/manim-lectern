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

## Alt text

Every structure has an `alt_text`: the words a student who can't see the slide gets
in place of the picture (handouts use it). By default it lists what's in the
structure. Set your own with `.with_alt("...")` when you create it, or
`x.alt_text = "..."` later. It stays until you set it again.

- If the script has an `alt:` line after the structure, use it word for word.
- Keep the automatic text for arrays, linked lists, stacks, rows, and small trees,
  where the contents *are* the point.
- Otherwise, write one: for every graph and net, for trees bigger than about seven
  nodes, and for anything the lecture uses as an example of something rather than
  for its exact contents.

Write it from the script around the structure, not from the picture:

- **Say what it's for.** Use the slide title, the bullets, and the `note:` lines.
  If the slide is "Cycles" and the notes say "notice we can get back to A", the alt
  text is about that cycle, not a list of every edge.
- **Include whatever the lecture points at.** If the narration says "the gray
  vertices" or "the third cell", the alt text has to say which vertices are gray or
  what's in the third cell, or the narration can't be followed.
- **Use the script's names.** If the script calls it "the house graph", so does the
  alt text.
- **Keep it short:** one to three sentences. Don't start with "An image of" or
  "A picture of"; screen readers already announce that it's an image.
- **Update it when the point changes.** After an animation changes what the slide is
  saying (a search finishes, a node is deleted), set new alt text, if the text you set
  earlier is no longer true.

```python
g = GraphView.from_file("house.gr").with_alt(
    "The house graph: a square A, B, C, D with a roof vertex E joined to A and B.")
...
self.play(*search_steps)
g.alt_text = "The house graph after depth-first search from A: every vertex is black."
```

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
