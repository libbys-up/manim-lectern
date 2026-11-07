# manim-lectern

Animated lecture slides from plain-text scripts, built on
[manim](https://www.manim.community/) and [manim-slides](https://manim-slides.eertmans.be/).

You write a lecture as a short script:

```
==== Linear Search
* Walk through the array and check each value
* Stop as soon as we find a match
\pause
[array: 3, 7, 2, 9, 4]
-- center --
highlight index 0, compare it to 9, and reject it
note: This is the search you'd do by hand on an unsorted list.
```

and it becomes a slide deck you present with `manim-slides present`: things appear
when you click, values move where they go, and speaker notes show in the presenter
view. The translation from script to Python is done by hand, by you or (more often)
by an AI coding agent, using the helpers in this library. The script markup is a set
of conventions, not a formal language, and you can change them for your course.

lectern grew out of about 130 lectures for three computer science courses (data
structures, algorithms, and compilers).

## What's here

| | |
|---|---|
| `src/lectern/` | the library: `SlideScene`, text, code, tables, themes, data structures |
| `src/lectern/extras/` | topic extensions: `parsing`, `assembly/mips`, `memory`, `semantics` |
| `src/lectern/conventions/SCRIPT_CONVENTIONS.md` | the script markup |
| `src/lectern/conventions/STYLE.md` | how slides should look and move (taste, not syntax) |
| `src/lectern/templates/course/` | starting files for a course folder (`lectern init` copies them) |
| `examples/` | scripts next to the lectures translated from them |
| `tools/themeify.py` | converts manim color names in existing code to theme roles |
| `tools/compare_slides.py` | compares two renders slide by slide, to check a change |

## Install

```
pip install -e path/to/manim-lectern
```

If you installed manim-slides with pipx, put lectern in the same environment:

```
pipx inject manim-slides -e path/to/manim-lectern
```

You also need LaTeX for math (see manim's installation guide).

## Quick start

```python
from manim import *
from lectern import *


class LinearSearch(SlideScene):
    def construct(self):
        a = Array([3, 7, 2, 9, 4])
        self.page("Linear Search",
            "* Walk through the array and check each value",
            "* Stop as soon as we find a match",
            P,                                   # \pause
            C(a),                                # centered
            lambda: self.play(a.set_background_cell(0, T.focus)),
            N("This is the search you'd do by hand."),  # speaker note
        )
```

```
manim-slides render -ql linear_search.py LinearSearch
manim-slides present LinearSearch
```

`page()` builds everything, scales it to fit, and then reveals it in order, so
nothing that's already shown moves and nothing runs off the screen. Run the examples:

```
cd examples
manim-slides render -ql lectures/linear_search.py LinearSearch
```

## Using an AI agent

In your course folder, run

```
lectern init
```

It creates `scripts/` and `lectures/`, and copies in an `AGENTS.md` (and a `CLAUDE.md`,
which points to it) tells an agent how to translate scripts, which conventions to
read, and how to check its work. Put your course's own rules in
`COURSE_CONVENTIONS.md`.

## Themes

Every color in lectern is a role (`T.focus`, `T.good`, `T.bad`, `T.current`,
`T.muted`, `T.text`, …), so one lecture renders in any theme. Built in: `dark`
(the default), `light`, `dark-colorblind`, and `light-colorblind` (using the
Okabe–Ito palette). Re-render without touching code:

```
LECTERN_THEME=dark-colorblind manim-slides render -qm lectures/bst.py Bst
```

Define your own in `lectern.toml`, starting from a built-in theme:

```toml
theme = "mine"

[themes.mine]
base = "dark"
focus = "#FFB000"
body_font = "Atkinson Hyperlegible"
```

To convert existing manim code, `python tools/themeify.py lectures/*.py` rewrites
color names as roles and lists anything it left alone.

## Checking layout

```
LECTERN_BOUNDS=/tmp/issues.txt manim-slides render -ql lectures/x.py X
```

writes a report of text that runs off the screen, overlaps other text, or has a line
through it, at each slide. It's approximate: it misses some problems and reports
some things that look fine. Use it to find slides worth looking at.

## Known workarounds

Every workaround for a manim or manim-slides problem is marked in the code with
`# WORKAROUND(<library> <version>)`. Find them all with `grep -rn WORKAROUND src`.

| where | what |
|---|---|
| `SlideScene.skip_reversing` | manim-slides 5.x crashes building reversed slide videos at -qm/-qh |
| `SlideScene.next_slide` | two slide breaks with nothing between them make an empty slide manim-slides can't join |
| `SlideScene.play` | an animation shorter than a frame fails at low quality; every animation lasts at least 0.2 s |
| `SlideScene.new_slide` | manim re-adds foreground mobjects, so they would survive a slide's fade-out |
| `SlideScene.add_mobjects_from_animations` | animating a group of parts of something on screen made manim pull that thing apart |
| `CodeHighlighter.set_lines` | manim counts an empty line as the point (0, 0) when sizing a group |

lectern also requires manim older than 0.21: manim 0.22 removed the `write_to_movie`
setting, and manim-slides 5.7 (the latest as of November 2026) still sets it, so the newest
releases of the two don't work together. Lift the limit in `pyproject.toml` once
manim-slides supports newer manim.

Rendering several lectures at once in the same folder can fail with "latex failed",
because they share the TeX cache in `media/`. Render that lecture again by itself.

## Contributing

See `AGENTS.md` (it's for people too). New extras are welcome, especially for
topics outside computer science.

## License

MIT. See `LICENSE`.
