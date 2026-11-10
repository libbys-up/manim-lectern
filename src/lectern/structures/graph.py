"""Helpers for driving DFS-style animations over Manim's built-in `Graph` mobject.

Unlike the other modules in `structures/`, this one does not define its own
`VGroup` -- it operates on a `manim.Graph` instance, providing the coloring
and adjacency helpers the DFS scenes need, plus a loader for the `.gr` graph
description files under `graphs/`.
"""

from collections import defaultdict
from typing import Dict, Optional, Tuple

from manim import Animation


def read_gr_file(path: str, weighted: Optional[bool] = None):
    """Parse a `.gr` file into `(vertices, edges, names)`.

    Format: a vertex block ("label, x, y" or "label, x, y, name" per line)
    separated by a blank line from an edge block. Each edge line is
    "source,target[,weight],target[,weight],..." -- a source vertex followed
    by its outgoing neighbors, either as a plain comma-separated list
    (`graphs/house.gr`) or as (neighbor, weight) pairs (`graphs/roads.gr`).

    Returns:
        vertices: dict mapping each label to a `[x, y, 0]` layout position,
            suitable for `manim.Graph(..., layout=vertices)`.
        edges: dict mapping each `(source, target)` pair to its weight (or
            `None` if the file didn't specify one). `edges.keys()` can be
            handed to `manim.Graph(...)` as the edge list.
        names: dict mapping each label to its display name (the label itself
            when the vertex line has no name column).

    `weighted` says how to read the edge lines. Leave it as `None` to detect it
    once for the whole file: the file counts as weighted only if *every* edge
    line is a list of (neighbor, number) pairs. Deciding per file rather than
    per line keeps numeric labels from being misread as weights, e.g. the
    Petersen files' "0,1,5" (edges 0-1 and 0-5), since their other lines like
    "5,7" can't be pairs. Pass True/False to override detection.
    """
    with open(path) as f:
        text = f.read()

    vertex_block, _, edge_block = text.partition("\n\n")

    vertices: Dict[str, list] = {}
    names: Dict[str, str] = {}
    for line in vertex_block.splitlines():
        line = line.strip()
        if not line:
            continue
        label, x, y, *rest = (field.strip() for field in line.split(","))
        vertices[label] = [float(x), float(y), 0]
        names[label] = rest[0] if rest else label

    edge_lines = []
    for line in edge_block.splitlines():
        line = line.strip()
        if line:
            source, *rest = (field.strip() for field in line.split(","))
            edge_lines.append((source, rest))

    def as_pairs(rest):
        if not rest or len(rest) % 2 != 0:
            return None
        try:
            return [(rest[i], float(rest[i + 1])) for i in range(0, len(rest), 2)]
        except ValueError:
            return None

    if weighted is None:
        weighted = bool(edge_lines) and all(as_pairs(rest) is not None for _, rest in edge_lines)

    edges: Dict[Tuple[str, str], Optional[float]] = {}
    for source, rest in edge_lines:
        if weighted:
            pairs = as_pairs(rest)
            if pairs is None:
                raise ValueError(f"{path}: edge line for {source!r} is not (neighbor, weight) pairs")
        else:
            pairs = [(target, None) for target in rest]

        for target, weight in pairs:
            edges[(source, target)] = weight

    return vertices, edges, names


def neighborhoods(g) -> Dict[str, list]:
    """Build an undirected adjacency map `{vertex: [neighbors]}` from a Graph's edges.

    Neighbors are listed in the order their edges appear in the graph (for a graph
    loaded from a .gr file, the order of the file), so a search that loops over them
    visits them in the same order on every render. To change the order a search
    takes, reorder the edges in the .gr file.

    (These used to be sets. Python changes the iteration order of a set of strings
    from one run to the next, so a search could take a different path each render.)"""
    adj = defaultdict(list)
    for u, v in g.edges:
        if v not in adj[u]:
            adj[u].append(v)
        if u not in adj[v]:
            adj[v].append(u)
    return adj


def change_color(g, v, color) -> Animation:
    return g.vertices[v][0].animate.set_fill(color, opacity=1, family=False)


def color_edge(g, v, u, color) -> Animation:
    if (v, u) in g.edges:
        return g.edges[(v, u)].animate.set_color(color)
    return g.edges[(u, v)].animate.set_color(color)


__all__ = ["read_gr_file", "neighborhoods", "change_color", "color_edge"]


# ---------------------------------------------------------------------------
# GraphView: a graph drawn for search algorithms (see the graph conventions)
# ---------------------------------------------------------------------------
#
# A hand-built VGroup rather than a wrapper around manim's Graph/DiGraph:
# DiGraph trims its arrows to each vertex's *bounding box* (so diagonal arrow
# tips float off the circle), and LabeledDot sizes itself from its label. Here
# every edge is trimmed to the circle outlines, arrowheads land exactly on the
# circle, and the WHITE / GRAY / BLACK / ring styling from the conventions
# lives in one place.
#
# Edge geometry is computed from the vertices' *current* centers by
# `redraw()`. Moving the whole GraphView (shift/scale/move_to) moves edges
# along with it; when individual vertices move, include `graph.follow()` (an
# UpdateFromFunc) in the same `play(...)` -- `move_to_layout` does that for you.

import os

import numpy as np
from manim import (
    BLACK, BLUE, DOWN, GREEN, GREY_A, GREY_B, GREY_C, GREY_D, GREY_E, LEFT, ORIGIN, RED,
    RIGHT, UP, WHITE, YELLOW, AnimationGroup, Circle, Create, Dot, FadeIn, FadeOut,
    ArcBetweenPoints, Line, Polygon, Rectangle, rotate_vector, ShowPassingFlash, Text, Transform, UpdateFromAlphaFunc, UpdateFromFunc,
    VGroup, VMobject,
)

from lectern.theme import T
from lectern.alt import AltText, count, describe_tree, words

def _state_style(state):
    """(fill, fill_opacity, stroke, label color) for a vertex state.

    "white", "gray", and "black" are the algorithm's names for a vertex's state
    (see the graph conventions), so their fills are those literal colors in every
    theme. Only "plain", the unmarked look, follows the theme."""
    return {
        "plain": (T.background, 1, T.text, T.text),
        "white": (WHITE, 1, T.text, BLACK),
        "gray": (GREY_C, 1, T.text, BLACK),
        "black": (BLACK, 1, GREY_C, WHITE),
    }[state]


class _StateStyles:
    """STATE_STYLE["gray"] etc., read from the active theme when used."""

    def __getitem__(self, state):
        return _state_style(state)


STATE_STYLE = _StateStyles()


class GraphVertex(VGroup):
    """A circle with its label inside (or, dots only, a small filled dot with
    a hidden label up and to the right of it)."""

    def __init__(self, name, text=None, radius=0.3, font_size=24, stroke_width=3,
                 dots_only=False, dot_radius=0.09):
        super().__init__()
        self.name = name
        self.dots_only = dots_only
        text = str(name) if text is None else str(text)
        if dots_only:
            self.circle = Dot(radius=dot_radius, color=T.text)
            self.label = Text(text, font_size=max(14, font_size * 0.7), color=GREY_A)
            self.label.next_to(self.circle, UP + RIGHT, buff=0.05)
            self.label.set_opacity(0)
        else:
            self.circle = Circle(radius=radius, color=T.text, stroke_width=stroke_width)
            self.circle.set_fill(T.background, opacity=1)
            self.label = Text(text, font_size=font_size, color=T.text)
            if self.label.width > 1.6 * radius:
                self.label.scale_to_fit_width(1.6 * radius)
            self.label.move_to(self.circle)
        self.add(self.circle, self.label)

    def center(self):
        return self.circle.get_center()

    @property
    def radius(self):
        return self.circle.width / 2


class GraphEdge(VGroup):
    """A line between two vertices, trimmed to their circles; directed edges
    get a filled triangular arrowhead that lands on the target circle."""

    def __init__(self, u, v, directed=False, color=None, stroke_width=3, tip_length=0.2, bend=0.0):
        color = T.text if color is None else color
        super().__init__()
        self.u, self.v = u, v
        self.directed = directed
        self.bend = bend
        self.tip_length = tip_length
        self.line = Line(LEFT, RIGHT, color=color, stroke_width=stroke_width)
        self.add(self.line)
        if directed:
            self.tip = Polygon(ORIGIN, RIGHT, UP, color=color, stroke_width=1)
            self.tip.set_fill(color, opacity=1)
            self.add(self.tip)

    def set_ends(self, start, end):
        d = end - start
        length = np.linalg.norm(d)
        if length < 1e-6:
            d = RIGHT * 1e-3
            length = 1e-3
        d = d / length
        if self.bend:
            # arc: the tip points along the arc's end tangent
            d = rotate_vector(d, self.bend / 2)
        if self.directed:
            n = np.array([-d[1], d[0], 0])
            L = min(self.tip_length, length * 0.6)
            base = end - d * L
            self.tip.set_points_as_corners([end, base + n * L * 0.45, base - n * L * 0.45, end])
            end = end - d * L * 0.8
        if self.bend:
            self.line.set_points(ArcBetweenPoints(start, end, angle=self.bend).get_points())
        else:
            self.line.put_start_and_end_on(start, end)

    def set_edge_opacity(self, opacity):
        """Opacity without filling in a curved edge (set_opacity would)."""
        self.line.set_stroke(opacity=opacity)
        if self.directed:
            self.tip.set_stroke(opacity=opacity).set_fill(opacity=opacity)
        return self

    def start(self):
        return self.line.get_start()

    def end(self):
        return self.tip.get_vertices()[0] if self.directed else self.line.get_end()


class GraphView(AltText, VGroup):
    """A drawn graph. Vertices are `GraphVertex`es keyed by name, edges are
    `GraphEdge`s keyed by (u, v) -- look them up with `vertex(v)` / `edge(u, v)`
    (undirected edges are found in either order).

    Methods that change the look return Animations (structures/ convention).
    """

    def __init__(self, positions, edges, directed=False, weights=None, labels=None,
                 dots_only=False, scale=1.0, radius=0.3, font_size=24, stroke_width=3,
                 edge_width=3, tip_length=0.2, dot_radius=0.09, weight_font_size=20,
                 weight_places=None, bends=None):
        super().__init__()
        self.directed = directed
        self.edge_width = edge_width
        self.weight_places = dict(weight_places or {})
        labels = labels or {}

        self.vertices = {}
        for v, p in positions.items():
            vert = GraphVertex(v, labels.get(v), radius=radius, font_size=font_size,
                               stroke_width=stroke_width, dots_only=dots_only, dot_radius=dot_radius)
            vert.shift(np.array(p, dtype=float) * scale - vert.center())
            self.vertices[v] = vert

        self.edges = {}
        for u, v in edges:
            if not directed and (v, u) in self.edges:
                continue
            bend = (bends or {}).get((u, v), -(bends or {}).get((v, u), 0.0))
            self.edges[(u, v)] = GraphEdge(u, v, directed=directed, stroke_width=edge_width,
                                           tip_length=tip_length, bend=bend)

        self.weights = {}
        self.weight_labels = {}
        for (u, v), w in (weights or {}).items():
            key = self._key(u, v)
            if key is None or w is None:
                continue
            self.weights[key] = w
            text = Text(_fmt(w), font_size=weight_font_size)
            bg = Rectangle(width=text.width + 0.12, height=text.height + 0.1,
                           stroke_width=0, fill_color=T.background, fill_opacity=1)
            self.weight_labels[key] = VGroup(bg, text)

        self.rings = {}
        self.state = {v: "plain" for v in self.vertices}

        self.edge_group = VGroup(*self.edges.values())
        self.weight_group = VGroup(*self.weight_labels.values())
        self.vertex_group = VGroup(*self.vertices.values())
        self.add(self.edge_group, self.weight_group, self.vertex_group)
        self.redraw()

    def say(self, v):
        """Vertex `v` as alt text names it: its label, or its key."""
        return self.vertices[v].label.text or str(v)

    def describe(self):
        """Lists every vertex and edge, and the search colors if any are set. For a
        graph of any size, a sentence about what it shows is usually better: set
        `alt_text`."""
        name = {v: self.say(v) for v in self.vertices}
        kind = "A directed" if self.directed else "An undirected"
        out = [f"{kind} graph with {count(len(name), 'vertex', 'vertices')}: {words(name.values())}."]
        if self.edges:
            join = "to" if self.directed else "and"
            parts = []
            for (u, v) in self.edges:
                w = self.weights.get((u, v))
                parts.append(f"{name[u]} {join} {name[v]}" + (f" (weight {_fmt(w)})" if w is not None else ""))
            out.append(f"{count(len(parts), 'edge').capitalize()}: {'; '.join(parts)}.")
        for state in ("white", "gray", "black"):
            marked = [name[v] for v, s in self.state.items() if s == state]
            if marked:
                out.append(f"{state.capitalize()}: {words(marked)}.")
        return " ".join(out)

    @classmethod
    def from_file(cls, path, directed=False, weighted=None, show_weights=None, **kwargs):
        """Load a `.gr` file. A bare file name is looked up in `graphs/` under the
        directory you render from (your course folder)."""
        if os.sep not in path:
            path = os.path.join("graphs", path)
        positions, edges, _names = read_gr_file(path, weighted=weighted)
        weights = {e: w for e, w in edges.items() if w is not None}
        if show_weights is False:
            weights = None
        return cls(positions, list(edges), directed=directed, weights=weights or None, **kwargs)

    # ---------- lookup ----------

    def _key(self, u, v):
        if (u, v) in self.edges:
            return (u, v)
        if not self.directed and (v, u) in self.edges:
            return (v, u)
        return None

    def vertex(self, v) -> GraphVertex:
        return self.vertices[v]

    def edge(self, u, v) -> GraphEdge:
        key = self._key(u, v)
        if key is None:
            raise KeyError(f"no edge {u}-{v}")
        return self.edges[key]

    def has_edge(self, u, v):
        return self._key(u, v) is not None

    def edge_label(self, u, v):
        return self.weight_labels[self._key(u, v)]

    def neighbors(self, v):
        """Neighbors in edge-list order (out-neighbors for a directed graph)."""
        out = []
        for a, b in self.edges:
            if a == v:
                out.append(b)
            elif b == v and not self.directed:
                out.append(a)
        return out

    def center_of(self, v):
        return self.vertices[v].center()

    def positions(self):
        return {v: vert.center() for v, vert in self.vertices.items()}

    # ---------- geometry ----------

    def _edge_ends(self, u, v):
        pu, pv = self.center_of(u), self.center_of(v)
        d = pv - pu
        n = np.linalg.norm(d)
        d = d / n if n > 1e-6 else RIGHT
        ru = self.vertices[u].radius if not self.vertices[u].dots_only else 0
        rv = self.vertices[v].radius if not self.vertices[v].dots_only else 0
        gap = 0.03 if self.directed else 0
        key = self._key(u, v)
        bend = self.edges[key].bend if key is not None else 0
        if key is not None and key != (u, v):
            bend = -bend
        return pu + rotate_vector(d, -bend / 2) * ru, pv - rotate_vector(d, bend / 2) * (rv + gap)

    def redraw(self):
        for (u, v), e in self.edges.items():
            e.set_ends(*self._edge_ends(u, v))  # (u, v) is the key: no bend flip
        for key, lab in self.weight_labels.items():
            lab.move_to(self._weight_point(*key))
        for (v, _color), ring in self.rings.items():
            ring.move_to(self.center_of(v))
        return self

    def _weight_point(self, u, v):
        t, side = self.weight_places.get((u, v), self.weight_places.get((v, u), (0.5, 1)))
        pu, pv = self.center_of(u), self.center_of(v)
        d = pv - pu
        d = d / max(np.linalg.norm(d), 1e-6)
        n = np.array([-d[1], d[0], 0])
        if n[1] < -1e-6 or (abs(n[1]) < 1e-6 and n[0] > 0):
            n = -n  # "side 1" is up (or left, for a vertical edge)
        return pu + (pv - pu) * t + n * 0.2 * side

    def follow(self):
        """Keep edges / weights / rings attached while vertices move."""
        return UpdateFromFunc(self, lambda m: m.redraw())

    def move_to_layout(self, positions, bends=None, **kwargs):
        """Slide each vertex in `positions` (scene coordinates) to its spot;
        edges follow. `bends` {(u, v): angle} curves those edges gradually
        on the way (e.g. so an edge can arc over vertices in a row)."""
        anims = [self.vertices[v].animate.shift(np.array(p) - self.center_of(v))
                 for v, p in positions.items()]
        if bends:
            edges = []
            for (u, v), angle in bends.items():
                e = self.edge(u, v)
                sign = 1 if self._key(u, v) == (u, v) else -1
                edges.append((e, e.bend, sign * angle))

            def bend(m, alpha):
                for e, a0, a1 in edges:
                    e.bend = a0 + (a1 - a0) * alpha

            anims.append(UpdateFromAlphaFunc(self, bend))
        return AnimationGroup(*anims, self.follow(), **kwargs)

    # ---------- vertex styling ----------

    def fill(self, v, color, label_color=None, stroke=None, opacity=1):
        label_color = BLACK if label_color is None else label_color  # dark text on a colored fill, in any theme
        vert = self.vertices[v]
        anims = [vert.circle.animate.set_fill(color, opacity=opacity)]
        if stroke is not None:
            anims[0] = vert.circle.animate.set_fill(color, opacity=opacity).set_stroke(stroke)
        if not vert.dots_only:
            anims.append(vert.label.animate.set_color(label_color))
        return AnimationGroup(*anims)

    def set_state(self, v, state):
        """'white' | 'gray' | 'black' (see the graph conventions), or 'plain'
        for the default unmarked look."""
        fill, opacity, stroke, label = _state_style(state)
        self.state[v] = state
        vert = self.vertices[v]
        if vert.dots_only:
            return vert.circle.animate.set_color({"gray": T.muted, "black": GREY_D}.get(state, T.text))
        return AnimationGroup(vert.circle.animate.set_fill(fill, opacity=opacity).set_stroke(stroke),
                              vert.label.animate.set_color(label))

    def whiten(self):
        """Mark every vertex WHITE right away (no animation), for a search that
        colors vertices WHITE / GRAY / BLACK. Returns self."""
        fill, opacity, stroke, label = _state_style("white")
        for v, vert in self.vertices.items():
            self.state[v] = "white"
            if not vert.dots_only:
                vert.circle.set_fill(fill, opacity=opacity).set_stroke(stroke)
                vert.label.set_color(label)
        return self

    def _make_ring(self, v, color, width=7, pad=0.07):
        r = self.vertices[v].radius + pad
        return Circle(radius=r, color=color, stroke_width=width).move_to(self.center_of(v))

    def ring(self, v, color=None, key=None, width=7):
        """Thick ring around `v` (BLUE = current, RED = target, GREEN = path).
        Rings are keyed by (vertex, key-or-color) so `move_ring` can slide one."""
        color = T.current if color is None else color
        key = (v, color if key is None else key)
        ring = self._make_ring(v, color, width=width)
        self.rings[key] = ring
        self.add(ring)
        return Create(ring)

    def unring(self, v, color=None, key=None):
        color = T.current if color is None else color
        key = (v, color if key is None else key)
        ring = self.rings.pop(key)
        self.remove(ring)
        return FadeOut(ring)

    def move_ring(self, v_from, v_to, color=None, key=None, along_edge=True):
        """Slide a ring from one vertex to another (along the edge between them)."""
        color = T.current if color is None else color
        k = color if key is None else key
        ring = self.rings.pop((v_from, k))
        self.rings[(v_to, k)] = ring
        target = self._make_ring(v_to, ring.get_color(), width=ring.get_stroke_width())
        return Transform(ring, target)

    def all_rings_off(self):
        anims = [FadeOut(r) for r in self.rings.values()]
        self.remove(*self.rings.values())
        self.rings = {}
        return AnimationGroup(*anims) if anims else AnimationGroup(FadeIn(VGroup()))

    def reset(self, state="plain"):
        """Every vertex back to `state` (default: unmarked), every edge back to white."""
        anims = [self.set_state(v, state) for v in self.vertices]
        anims += [e.animate.set_color(T.text).set_stroke(width=self.edge_width).set_edge_opacity(1)
                  for e in self.edges.values()]
        return AnimationGroup(*anims)

    # ---------- edge styling ----------

    def color_edge(self, u, v, color, width=None):
        e = self.edge(u, v)
        width = self.edge_width * 1.7 if width is None and color != T.text else (width or self.edge_width)
        return e.animate.set_color(color).set_stroke(width=width)

    def flash_edge(self, u, v, color=None, width=None, run_time=0.6):
        """A bright streak running from u to v along the edge (checking it)."""
        color = T.focus if color is None else color
        e = self.edge(u, v)
        a, b = self._edge_ends(u, v)
        streak = Line(a, b, color=color, stroke_width=width or self.edge_width * 3)
        if e.bend:
            sign = 1 if self._key(u, v) == (u, v) else -1
            streak = ArcBetweenPoints(a, b, angle=sign * e.bend, color=color,
                                      stroke_width=width or self.edge_width * 3)
        return ShowPassingFlash(streak, time_width=0.6, run_time=run_time)

    def highlight_edge_glow(self, u, v, color=None):
        color = T.focus if color is None else color
        return self.color_edge(u, v, color)

    # ---------- dots ----------

    def show_dot_labels(self):
        return AnimationGroup(*[vert.label.animate.set_opacity(1) for vert in self.vertices.values()])

    def to_dots(self, dot_radius=0.09):
        """Shrink every labeled circle to a small filled dot and fade its label."""
        anims = []
        for vert in self.vertices.values():
            dot = Dot(radius=dot_radius, color=T.text).move_to(vert.center())
            anims.append(Transform(vert.circle, dot))
            anims.append(vert.label.animate.set_opacity(0))
        return AnimationGroup(*anims, self.follow())


def _fmt(w):
    return str(int(w)) if float(w).is_integer() else str(w)


__all__ += ["GraphView", "GraphVertex", "GraphEdge", "STATE_STYLE"]
