"""`SlideScene`: the base class for a lecture. It's a manim-slides `Slide` with
methods named after the script markup in conventions/SCRIPT_CONVENTIONS.md.

Most slides are one call:

    from lectern import *

    class Intro(SlideScene):
        def construct(self):
            self.page("What a compiler does",
                "A compiler *translates* a program.",
                P,
                "* from a source language",
                "* to a target language",
            )

`page()` and `panes()` lay everything out first, scale it to fit, and then reveal
it, so things revealed earlier never move and nothing runs off the screen. See
markers.py for P (pause), N (speaker note), C (center), and H (place but hide).
"""

import numpy as np
from manim import (DOWN, LEFT, RIGHT, UP, AnimationGroup, Arrow, Circle, Code, Create, Dot, FadeIn, FadeOut, Group, Indicate, LaggedStart,
                   Line, MarkupText, MathTex, Polygon, Rectangle, ReplacementTransform, Square, Tex, Text, VGroup, config)
from manim_slides import Slide

from lectern import boxes as _boxes
from lectern import bounds, text as _text
from lectern.code import CodeMixin, background_kwargs
from lectern.markers import C, H, N, P
from lectern.settings import (BODY_FONT_SIZE, BOTTOM, MARGIN, MIN_RUN_TIME, MIN_SCALE, PANE_FONT_SIZE, STEP,
                              TITLE_FONT_SIZE, TOP_BUFF, WARN_SCALE)
from lectern.table import grid_table as _grid_table
from lectern.table import table as _table
from lectern.theme import T, use_theme

__all__ = ["SlideScene"]

# Shapes whose default color should follow the theme's text color. manim's default
# for these is white, which vanishes on a light background.
_THEMED_DEFAULTS = (Text, MarkupText, Tex, MathTex, Line, Dot, Circle, Arrow, Rectangle, Square, Polygon)


class SlideScene(CodeMixin, Slide):
    """See the module docstring. Set `theme = "light"` (or any theme name) on a
    subclass to choose its theme; LECTERN_THEME still overrides it."""

    theme = None
    title = None
    margin = MARGIN  # left and right page margins; a course can set its own

    # WORKAROUND(manim-slides 5.x): building the reversed copy of each slide video
    # crashes at -qm and -qh ("non monotonically increasing dts") on the slightly
    # uneven timestamps of stitched clips. Reversed videos are only used for smooth
    # backward playback in the presenter, so skip them.
    skip_reversing = True

    def setup(self):
        super().setup()
        use_theme(self.theme)
        self.camera.background_color = T.background
        if T.text.to_hex() != "#FFFFFF":
            for cls in _THEMED_DEFAULTS:
                cls.set_default(color=T.text)

    # ---------------------------------------------------------------- slides

    def slide_title(self, text, font_size=TITLE_FONT_SIZE):
        return Text(text, font_size=font_size, color=T.text).to_edge(UP)

    def new_slide(self, title_text):
        """`==== Title`: advance, fade out everything on screen, bring in the title."""
        if self.mobjects:
            self.next_slide()
            # WORKAROUND(manim 0.20): Scene.add re-adds every foreground mobject, so one
            # still on that list would survive the fade and come back on the next slide.
            self.foreground_mobjects = []
            self.play(FadeOut(Group(*self.mobjects)))
        self._line_marks = None
        self.title = self.slide_title(title_text)
        self.play(FadeIn(self.title))
        return self.title

    def continue_slide(self, title_text, keep=()):
        """Like new_slide, but the mobjects in `keep` stay where they are, and the old
        title turns into the new one: for a diagram that carries over to the next slide."""
        self.next_slide()
        self._line_marks = None
        others = [m for m in self.mobjects if m not in keep and m is not self.title]
        new_title = self.slide_title(title_text)
        anims = [FadeOut(Group(*others))] if others else []
        # WORKAROUND(manim 0.20): see new_slide; foreground mobjects not kept would come back.
        self.foreground_mobjects = [m for m in self.foreground_mobjects if m in keep]
        self.play(*anims, ReplacementTransform(self.title, new_title))
        self.title = new_title
        return new_title

    def clear_body(self):
        """Fade out everything but the title: an untitled continuation (a bare `====`)."""
        rest = [m for m in self.mobjects if m is not self.title]
        if rest:
            self.play(FadeOut(Group(*rest)))

    def add_mobjects_from_animations(self, animations):
        # WORKAROUND(manim 0.20): before playing, Scene adds each animation's mobject
        # if it isn't on screen. For an AnimationGroup that mobject is a wrapper Group
        # of the members; adding a wrapper whose members already belong to something on
        # screen (a GraphView's vertex circles, say) makes manim pull that parent apart.
        # So for wrapper Groups, add only the members that are new.
        on_screen = {id(m) for m in self.get_mobject_family_members()}

        def add(mob):
            if mob is None or id(mob) in on_screen:
                return
            if type(mob) is Group:
                for sub in mob.submobjects:
                    add(sub)
                return
            self.add(mob)
            on_screen.update(id(m) for m in mob.get_family())

        for animation in animations:
            if animation.is_introducer():
                continue
            mob = animation.mobject
            if isinstance(animation, AnimationGroup):
                add(mob)
            elif mob is not None and id(mob) not in on_screen:
                # e.g. FadeOut(Group(*self.mobjects)): the Group itself has to be added,
                # so the remove at the end takes its members with it.
                self.add(mob)
                on_screen.update(id(m) for m in mob.get_family())

    def pause(self):
        """`\\pause`: advance without fading anything."""
        self.next_slide()

    def next_slide(self, *args, **kwargs):
        # WORKAROUND(manim-slides 5.x): two slide breaks with no animation between
        # them make an empty slide, which manim-slides can't concatenate. Skip the
        # second break.
        plays = self.renderer.num_plays
        if plays == getattr(self, "_plays_at_slide", -1):
            return None
        self._plays_at_slide = plays
        bounds.check(self)
        return super().next_slide(*args, **kwargs)

    def play(self, *args, **kwargs):
        # WORKAROUND(manim 0.20): a very short animation rounds to zero frames at low
        # quality and the render fails, so give every animation at least MIN_RUN_TIME.
        if "run_time" in kwargs:
            kwargs["run_time"] = max(kwargs["run_time"], MIN_RUN_TIME)
        return super().play(*args, **kwargs)

    def note(self, text):
        """`note: ...`: add `text` to the speaker notes of the slide being built."""
        cfg = self._base_slide_config
        cfg.notes = f"{cfg.notes}\n{text}" if cfg.notes else text

    def handout(self, name):
        """A small tag in the corner: the full version of what's on screen is in this handout."""
        tag = Text(f"Full version: {name}" if name.endswith(".pdf") else name, font_size=20,
                   color=T.subtle).to_corner(DOWN + RIGHT, buff=0.25)
        self.show(tag, rt=0.3)
        return tag

    # ---------------------------------------------------------------- text

    def markup(self, text):
        return _text.markup(text)

    def styled(self, text, font_size=PANE_FONT_SIZE, color=None):
        return _text.styled(text, font_size, color)

    def mixed(self, text, font_size=PANE_FONT_SIZE, color=None):
        return _text.mixed(text, font_size, color)

    def split_lines(self, text, font_size, max_w):
        return _text.split_lines(text, font_size, max_w)

    def txt(self, text, font_size=PANE_FONT_SIZE, color=None, max_w=12.8):
        return _text.txt(text, font_size, color, max_w)

    def item(self, s, font_size, max_w):
        return _text.item(s, font_size, max_w)

    def math_text(self, tex, font_size=PANE_FONT_SIZE, color=None, **kwargs):
        """A `text:` line that is math: real LaTeX, not prose with markup. For an equation
        that changes step by step, build it from several math_text pieces and move them
        (see "Algebraic transformations" in SCRIPT_CONVENTIONS.md)."""
        return MathTex(tex, font_size=font_size, color=color or T.text, **kwargs)

    def bullets(self, items, font_size=PANE_FONT_SIZE, buff=0.28, indent=0.5, ordered=False, label=None):
        """A list as one VGroup. items: str, or (str, depth) for nested items.
        Markers step • ◦ ▪ by depth, or 1. a. i. with ordered=True. `label` adds a
        heading line above the list."""
        rows = VGroup()
        depths = []
        counters = {}
        for it in items:
            s, depth = it if isinstance(it, tuple) else (it, 0)
            if ordered:
                for deeper in [d for d in counters if d > depth]:  # a new sub-list restarts at 1
                    del counters[deeper]
                counters[depth] = counters.get(depth, 0) + 1
                marker = _text.ordinal(depth, counters[depth])
            else:
                marker = _text.BULLETS[min(depth, len(_text.BULLETS) - 1)]
            rows.add(self.styled(f"{marker} {s}", font_size=font_size))
            depths.append(depth)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=buff)
        for row, depth in zip(rows, depths):
            row.shift(RIGHT * indent * depth)
        if label is not None:
            heading = self.styled(label, font_size=font_size + 4)
            heading.next_to(rows, UP, buff=buff * 1.5, aligned_edge=LEFT)
            rows = VGroup(heading, rows)
        return rows

    # ---------------------------------------------------------------- boxes and tables

    def definition_box(self, label, lines, font_size=28, width=None, pad=0.35, max_w=12.0):
        return _boxes.definition_box(label, lines, font_size, width, pad, max_w)

    box = definition_box

    def compact_box(self, label, lines, font_size=24, max_w=6.0):
        return _boxes.compact_box(label, lines, font_size, max_w)

    def term(self, text, font_size=22, width=None):
        return _boxes.term(text, font_size, width)

    def red_x(self, mob):
        return _boxes.red_x(mob)

    def surround(self, mob, color=None, buff=0.06):
        return _boxes.surround(mob, color, buff)

    def lit_box(self, b, color=None, opacity=0.35):
        return _boxes.lit_box(b, color, opacity)

    def table(self, rows, font_size=24, header=True, gap_x=0.5, gap_y=0.18):
        return _table(rows, font_size, header, gap_x, gap_y)

    def grid_table(self, rows, font_size=26, header=True, h_buff=0.6, v_buff=0.28, cell=None, line_config=None):
        return _grid_table(rows, font_size, header, h_buff, v_buff, cell, line_config)

    def reveal_grid_table(self, t, pause_between=True):
        """Show a grid_table: the grid and header row, then each row (pausing before each)."""
        rows = t.get_rows()
        self.play(Create(VGroup(t.get_horizontal_lines(), t.get_vertical_lines())), FadeIn(rows[0]))
        for row in rows[1:]:
            if pause_between:
                self.pause()
            self.play(FadeIn(row))

    def rows(self, t):
        """For page(): reveal a table placed with H(t), one row per pause."""

        def go():
            for i, r in enumerate(t.rows_):
                self.play(FadeIn(r), run_time=0.35)
                if 0 < i < len(t.rows_) - 1:
                    self.pause()

        return go

    def code_block(self, path, scale=0.6, language="c"):
        """A code block read from a file (pair it with CodeHighlighter)."""
        return Code(path, tab_width=4, language=language, formatter_style=T.code_style, **background_kwargs()).scale(scale)

    # ---------------------------------------------------------------- page layout

    def top_y(self):
        return self.content_top(TOP_BUFF)

    def content_top(self, buff=0.45):
        """The y just below the title (or the top of the frame if there's no title)."""
        return (self.title.get_bottom()[1] if self.title is not None else config.frame_height / 2) - buff

    def layout(self, items, x0, x1, top, bottom, font_size=PANE_FONT_SIZE, buff=0.26, center=False):
        """Build `items`, stack them in the region x0..x1, top..bottom, and scale them
        to fit. Returns (sequence for run(), the mobjects)."""
        seq, mobs, flags = [], [], []
        for it in items:
            if it is P or callable(it) or isinstance(it, N):
                seq.append(it)
                continue
            hidden, is_c = False, center
            raw = it
            while isinstance(raw, (C, H)):
                hidden = hidden or isinstance(raw, H)
                is_c = is_c or isinstance(raw, C) or (isinstance(raw, H) and raw.center)
                raw = raw.mob
            if isinstance(raw, str):
                # An empty string is a small vertical gap.
                mob = self.item(raw, font_size, x1 - x0) if raw else Rectangle(width=0.01, height=0.15, stroke_opacity=0)
                is_c = isinstance(it, C)
            else:
                mob = raw
            if not hidden:
                seq.append(mob)
            mobs.append(mob)
            flags.append(is_c)
        if not mobs:
            return seq, mobs
        y = 0.0
        for m in mobs:
            m.shift(UP * (y - m.get_top()[1]))
            y = m.get_bottom()[1] - buff
        group = VGroup(*mobs)
        width, height = x1 - x0, top - bottom
        k = min(1.0, width / max(m.width for m in mobs), height / group.height) if height > 0 else 0.0
        # Never shrink past MIN_SCALE. Running off the page gets reported, but a
        # sentence scaled down to a speck just looks like nothing is wrong.
        if k < MIN_SCALE:
            bounds.report(self, f"SHRINK k={k:.2f} floored at {MIN_SCALE}")
            k = MIN_SCALE
        elif k < WARN_SCALE:
            bounds.report(self, f"SHRINK k={k:.2f}")
        if k < 1.0:
            for m in mobs:
                m.scale(k, about_point=np.zeros(3))
        for m, c in zip(mobs, flags):
            if c:
                m.set_x((x0 + x1) / 2)
            else:
                m.shift(RIGHT * (x0 - m.get_left()[0]))
        group.shift(UP * (top - group.get_top()[1]))
        return seq, mobs

    def run(self, seq):
        """Reveal a sequence from layout(): mobjects fade in together until a P,
        a note, or a callable."""
        batch = []

        def flush():
            if batch:
                self.play(*[self.show_anim(m) for m in batch], run_time=STEP)
                batch.clear()

        for s in seq:
            if s is P:
                flush()
                self.pause()
            elif isinstance(s, N):
                self.note(s.text)
            elif callable(s):
                flush()
                s()
            else:
                batch.append(s)
        flush()

    def show_anim(self, m):
        """How page() reveals each item. Override for a different entrance."""
        return FadeIn(m)

    def page(self, title, *items, font_size=BODY_FONT_SIZE, buff=0.28, center=False, bottom=BOTTOM):
        """A new slide titled `title` (None: keep the current slide), with `items`
        stacked down the page. See the module docstring."""
        if title is not None:
            self.new_slide(title)
        hw = config.frame_width / 2
        seq, mobs = self.layout(items, -hw + self.margin, hw - self.margin, self.top_y(), bottom, font_size, buff, center)
        self.run(seq)
        self.last_mobs = mobs
        return mobs

    def recap_page(self, *items):
        return self.page("Recap", *items)

    def panes(self, title, left=(), right=(), below=(), split=0.0, font_size=PANE_FONT_SIZE, order="lr", top=None,
              bottom=BOTTOM, gap=0.5):
        """Two columns, split at x=`split`, then an optional full-width block under
        both. Everything is placed first, then revealed: left, right, below
        (order="rl" reveals the right column first)."""
        if title is not None:
            self.new_slide(title)
        hw = config.frame_width / 2
        t = self.top_y() if top is None else top
        bot = bottom
        bseq, bmobs = [], []
        if below:
            bseq, bmobs = self.layout(below, -hw + self.margin, hw - self.margin, 0, -10, font_size)
            need = VGroup(*bmobs).height + 0.3 if bmobs else 0
            bot = bottom + need
        lseq, lmobs = self.layout(left, -hw + self.margin, split - gap / 2, t, bot, font_size)
        rseq, rmobs = self.layout(right, split + gap / 2, hw - self.margin, t, bot, font_size)
        if bmobs:
            lowest = min([m.get_bottom()[1] for m in lmobs + rmobs] or [t])
            VGroup(*bmobs).shift(UP * (lowest - 0.3 - VGroup(*bmobs).get_top()[1]))
        for s in (lseq + rseq if order == "lr" else rseq + lseq) + bseq:
            self.run([s])
        return lmobs, rmobs, bmobs

    def more(self, *items, font_size=BODY_FONT_SIZE, buff=0.28, x=None, x1=None, center=False, bottom=BOTTOM, after=None):
        """Continue the slide under `after` (default: the last thing page() showed)."""
        ref = after if after is not None else (self.last_mobs[-1] if getattr(self, "last_mobs", None) else self.title)
        top = ref.get_bottom()[1] - buff
        hw = config.frame_width / 2
        x0 = -hw + self.margin if x is None else x
        seq, mobs = self.layout(items, x0, hw - self.margin if x1 is None else x1, top, bottom, font_size, buff, center)
        self._avoid(mobs, buff)
        self.run(seq)
        self.last_mobs = (getattr(self, "last_mobs", None) or []) + mobs
        return mobs

    def _avoid(self, mobs, buff=0.2):
        """Move a new block down until it's clear of everything already on screen."""
        if not mobs:
            return
        block = VGroup(*mobs)
        others = [m for m in self.mobjects if m is not self.title and (m.has_points() or m.submobjects)]
        for _ in range(8):
            hits = [m for m in others if bounds.boxes_hit(block, m)]
            if not hits:
                break
            block.shift(DOWN * (block.get_top()[1] - min(m.get_bottom()[1] for m in hits) + min(buff, 0.2)))
        if block.get_bottom()[1] < -config.frame_height / 2:
            bounds.report(self, f"NO ROOM for {bounds.name_of(mobs[0])!r}")

    def right_of(self, *items, ref, font_size=28, gap=0.5, top=None):
        """A column in the space to the right of `ref`."""
        hw = config.frame_width / 2
        t = self.top_y() if top is None else top
        seq, mobs = self.layout(items, ref.get_right()[0] + gap, hw - self.margin, t, BOTTOM, font_size)
        self._avoid(mobs)
        self.run(seq)
        return mobs

    # Simpler placement, for slides built by hand: the `-- anchor --` and
    # `<< direction` directives in SCRIPT_CONVENTIONS.md.

    def content_area(self, title_buff=1.6):
        """(top, bottom, left, right) of the region below the title, inside the margins."""
        hw, hh = config.frame_width / 2, config.frame_height / 2
        return hh - title_buff, -hh + self.margin, -hw + self.margin, hw - self.margin

    def anchor(self, mob, position):
        """`-- position --`: move `mob` to a named region of the content area: left,
        right, up, down, center, or a corner ("up left", "down right", ...)."""
        top, bottom, left, right = self.content_area()
        parts = position.split()
        cx = {"left": left + mob.width / 2, "right": right - mob.width / 2}
        cy = {"up": top - mob.height / 2, "down": bottom + mob.height / 2}
        x = next((cx[p] for p in parts if p in cx), (left + right) / 2)
        y = next((cy[p] for p in parts if p in cy), (top + bottom) / 2)
        return mob.move_to(np.array([x, y, 0]))

    def anchor_point(self, position, inset=1.5):
        """The point for a named region (see `anchor`), for a structure that will grow
        after it's shown: pass it as `start_point=` so the *finished* structure lands
        there. `inset` keeps an edge point that far in from the edge."""
        top, bottom, left, right = self.content_area()
        parts = position.split()
        cx = {"left": left + inset, "right": right - inset}
        cy = {"up": top - inset, "down": bottom + inset}
        x = next((cx[p] for p in parts if p in cx), (left + right) / 2)
        y = next((cy[p] for p in parts if p in cy), (top + bottom) / 2)
        return np.array([x, y, 0])

    def next_to_prev(self, mob, prev, direction, buff=None, aligned_edge=None):
        """`<< direction`: put `mob` left, right, up, or down of `prev`. Up and down keep
        left edges aligned, so the default flow stays left-justified."""
        units = {"left": LEFT, "right": RIGHT, "up": UP, "down": DOWN}
        buff = self.margin if buff is None else buff
        if aligned_edge is None:
            aligned_edge = LEFT if direction in ("up", "down") else np.zeros(3)
        return mob.next_to(prev, units[direction], buff=buff, aligned_edge=aligned_edge)

    def place_first(self, mob, buff=0.45):
        """First block of a slide: against the left margin, just below the title."""
        mob.to_edge(LEFT, buff=self.margin)
        mob.shift(UP * (self.content_top(buff) - mob.get_top()[1]))
        return mob

    def place_below(self, mob, prev, buff=0.3):
        """`<< down`: under `prev`, left edges aligned."""
        return mob.next_to(prev, DOWN, buff=buff, aligned_edge=LEFT)

    def place_pane(self, mob, side, top=None, buff=0.45):
        """Center `mob` in the left or right half of the frame, top edge at `top`
        (default: just below the title)."""
        top = self.content_top(buff) if top is None else top
        x = config.frame_width / 4 * (-1 if side == "left" else 1)
        mob.move_to(np.array([x, top - mob.height / 2, 0]))
        return mob

    def fit(self, mob, max_width=None, max_height=None):
        """Scale `mob` down (never up) to fit."""
        if max_width is not None and mob.width > max_width:
            mob.scale_to_fit_width(max_width)
        if max_height is not None and mob.height > max_height:
            mob.scale_to_fit_height(max_height)
        return mob

    def fit_box(self, mob, left, right, top, bottom, align="center"):
        """Scale `mob` down (never up) to fit the box, then place it there: centered
        (default), at the top ("up"), or with its top left at the box's ("up left")."""
        self.fit(mob, max_width=right - left, max_height=top - bottom)
        if align == "center":
            mob.move_to([(left + right) / 2, (top + bottom) / 2, 0])
        elif align == "up":
            mob.move_to([(left + right) / 2, top - mob.height / 2, 0])
        else:  # "up left"
            mob.move_to([left + mob.width / 2, top - mob.height / 2, 0])
        return mob

    def left_pane(self, mob, top=None, split=0.0, align="center", bottom=BOTTOM):
        """Fit `mob` into the left of the slide, up to x=`split`: a structure next to text."""
        top = self.content_top() if top is None else top
        return self.fit_box(mob, -config.frame_width / 2 + self.margin, split - 0.2, top, bottom, align)

    def right_pane(self, mob, top=None, split=0.0, align="up left", bottom=BOTTOM):
        """Fit `mob` into the right of the slide, from x=`split`."""
        top = self.content_top() if top is None else top
        return self.fit_box(mob, split + 0.2, config.frame_width / 2 - self.margin, top, bottom, align)

    # ---------------------------------------------------------------- showing things

    def show(self, *mobs, rt=STEP):
        self.play(*[FadeIn(m) for m in mobs], run_time=rt)

    def hide(self, *mobs, rt=STEP):
        mobs = [m for m in mobs if m is not None]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=rt)

    def go(self, *anims, rt=STEP):
        """Play animations together. Lists are flattened and None is skipped, so
        helpers that return lists of animations can be passed straight in."""
        flat = []
        for a in anims:
            if isinstance(a, (list, tuple)):
                flat.extend(a)
            elif a is not None:
                flat.append(a)
        if flat:
            self.play(*flat, run_time=max(rt, MIN_RUN_TIME))

    def reveal(self, mob, lag_ratio=0.15):
        """Fade in `mob`; a group's members come in one after another."""
        self.play(self.fade_in_group(mob, lag_ratio))

    def fade_in_group(self, group, lag_ratio=0.15):
        """Animation: fade in a group's members one after another."""
        if isinstance(group, VGroup) and len(group) > 1:
            return LaggedStart(*[FadeIn(m) for m in group], lag_ratio=lag_ratio)
        return FadeIn(group)

    def fly(self, source, dest, rt=STEP, keep=False, copy=True, color=None):
        """A copy of `source` moves to `dest`. Returns the copy (still on screen if keep)."""
        m = source.copy() if copy else source
        if color is not None:
            m.set_color(color)
        self.add(m)
        self.play(m.animate.move_to(dest), run_time=rt)
        if not keep:
            self.remove(m)
        return m

    def into(self, source, dest):
        """Animation: a copy of `source` becomes `dest`."""
        return ReplacementTransform(source.copy(), dest)

    def carry(self, mob):
        """Keep a copy of a value on screen, e.g. one popped into a register that isn't
        drawn, so it can move on later: pass it as `src=` and it goes away when it moves."""
        m = mob.copy()
        m.carried = True
        self.add(m)
        return m

    def flash(self, mob, color=None):
        self.play(Indicate(mob, color=color or T.focus), run_time=STEP)

    def nodes(self, t, *keys):
        """Animation: fade in nodes of a LabelTree, with the edges above them."""
        parts = VGroup()
        for k in keys:
            i = t.idx(k)
            parts.add(t.nodes_[i])
            if i in t.edge_of:
                parts.add(t.edges_[t.edge_of[i]])
        return FadeIn(parts)

    def recap(self, items, font_size=32):
        """A "Recap" slide with a bullet list."""
        self.new_slide("Recap")
        b = self.place_first(self.bullets(items, font_size=font_size, buff=0.35), buff=0.7)
        self.play(self.fade_in_group(b))
