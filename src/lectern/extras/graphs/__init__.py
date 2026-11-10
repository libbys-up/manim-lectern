"""Graph theory: named graphs, the script's graph notation, highlighting, walks,
layout morphs, and the three representations drawn next to a graph.

    from lectern.extras.graphs import *

    g = house()                                   # the house graph, a-e
    m = AdjacencyMatrix.from_graph(g)             # 5x5 grid with row/column names
    l = AdjacencyList.from_graph(g)               # a -> [b][c] ...
    self.page("Houses", C(g), P,
              lambda: self.play(g.light(["a", "b"], [("a", "b")])),
              P,
              lambda: self.play(g.unlight_all(), g.walk("bacbdec")),
              P,
              lambda: self.play(g.morph_to(flipped(HOUSE_LAYOUT))))

    s = petersen("star")
    self.play(s.morph_to(PETERSEN_CIRCLE_LAYOUT, bends=PETERSEN_CIRCLE_BENDS))

Graphs are `DrawnGraph`s, a `GraphView` (lectern.structures.graph) with the
methods graph theory lectures need. Every method that changes the drawing returns
an animation, as everywhere in lectern.

Script notation (see CONVENTIONS.md in this folder):

    Graph[[a,b,c], [(a,b),(b,c)]]        graph_from(*parse_graph(text))
    AdjGraph{a : [b,c], b : [a,c]}       adj_graph(text)
    K_n E_n C_n P_n Q_n                  complete(n) empty(n) cycle(n) path(n) cube(n)
    house, petersenStar/petersenCircle   house(), petersen("star"/"circle")

Conventions: CONVENTIONS.md in this folder.
"""

import math
import re

import numpy as np
from manim import (
    DOWN, LEFT, RIGHT, UP, AnimationGroup, Arrow, Circle, FadeIn, FadeOut, Rectangle,
    Succession, Text, TransformFromCopy, VGroup, Wait,
)

from lectern.alt import AltText, count, words
from lectern.structures.graph import GraphView
from lectern.text import mono
from lectern.theme import T

__all__ = [
    "DrawnGraph", "AdjacencyMatrix", "AdjacencyList", "EdgeList",
    "parse_adj", "parse_graph", "parse_matrix", "adj_edges",
    "graph_from", "adj_graph", "empty", "complete", "cycle", "path", "cube", "bipartite",
    "house", "petersen",
    "circle_layout", "line_layout", "cube_layout", "bipartite_layout", "rings_layout", "flipped",
    "HOUSE_ADJ", "HOUSE_LAYOUT", "HOUSE_WEIGHTS", "DIRECTED_HOUSE", "PETERSEN_STAR_LAYOUT",
    "PETERSEN_CIRCLE_LAYOUT", "PETERSEN_CIRCLE_BENDS", "PETERSEN_NUMBERS",
    "bfs_levels", "kruskal",
]


# ---------------------------------------------------------------------------
# The script's notation
# ---------------------------------------------------------------------------

_NAME = r"[^\s,\[\]{}():]+"


def parse_adj(text):
    """`AdjGraph{a : [b,c], b : [a,c]}` (or just the `{...}` part, or a dict) to an
    ordered dict {vertex: [neighbors]}, every name a string. Neighbor order is kept:
    it's the order a loop over the neighborhood visits them."""
    if isinstance(text, dict):
        return {str(v): [str(u) for u in us] for v, us in text.items()}
    body = text.strip()
    body = body[body.index("{") + 1: body.rindex("}")]
    adj = {}
    for v, us in re.findall(rf"({_NAME})\s*:\s*\[([^\]]*)\]", body):
        adj[v] = re.findall(_NAME, us)
    return adj


def parse_graph(text):
    """`Graph[[a,b,c], [(a,b),(b,c)]]` to (vertices, edges)."""
    body = text.strip()
    body = body[body.index("[") + 1: body.rindex("]")]
    vs_text, _, es_text = body.partition("]")
    vertices = re.findall(_NAME, vs_text)
    edges = [tuple(p) for p in re.findall(rf"\(\s*({_NAME})\s*,\s*({_NAME})\s*\)", es_text)]
    return vertices, edges


def parse_matrix(text):
    """The script's LaTeX-ish matrix rows (`0 & 1 & 1 \\\\` per line) to a list of
    lists of strings."""
    rows = []
    for line in re.split(r"\\\\|\n", text):
        cells = [c.strip() for c in line.split("&")]
        if any(cells):
            rows.append(cells)
    return rows


def adj_edges(adj, directed=False):
    """Edges of an adjacency dict, in neighborhood order. Undirected: each edge once."""
    edges, seen = [], set()
    for v, us in adj.items():
        for u in us:
            key = (v, u) if directed else frozenset((v, u))
            if key not in seen:
                seen.add(key)
                edges.append((v, u))
    return edges


# ---------------------------------------------------------------------------
# Layouts: {vertex: (x, y)}, about 4 units across
# ---------------------------------------------------------------------------

def circle_layout(vertices, radius=2.0, start=90):
    """Evenly around a circle, the first at `start` degrees, going clockwise."""
    vertices = list(vertices)
    n = max(len(vertices), 1)
    out = {}
    for i, v in enumerate(vertices):
        a = math.radians(start - 360 * i / n)
        out[v] = (radius * math.cos(a), radius * math.sin(a))
    return out


def line_layout(vertices, gap=1.3):
    """Left to right in a row (paths)."""
    vertices = list(vertices)
    x0 = -gap * (len(vertices) - 1) / 2
    return {v: (x0 + gap * i, 0) for i, v in enumerate(vertices)}


# one direction per cube dimension; Q_4 is two cubes side by side
_CUBE_DIRS = [(2.0, 0.0), (0.0, 2.0), (1.0, 0.8), (3.6, -1.3), (-1.2, 3.4)]


def cube_layout(n):
    """Q_n as the usual n-dimensional cube drawing; vertices are bit strings."""
    out = {}
    for bits in range(2 ** n):
        name = format(bits, f"0{n}b") if n else "0"
        x = y = 0.0
        for d in range(n):
            if bits >> (n - 1 - d) & 1:
                x += _CUBE_DIRS[d][0]
                y += _CUBE_DIRS[d][1]
        out[name] = (x, y)
    xs = [p[0] for p in out.values()]
    ys = [p[1] for p in out.values()]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return {v: (x - cx, y - cy) for v, (x, y) in out.items()}


def bipartite_layout(top, bottom, gap=1.4, height=2.4):
    """Two rows: `top` above `bottom`, so every edge crosses between them."""
    out = {}
    for row, y in ((list(top), height / 2), (list(bottom), -height / 2)):
        x0 = -gap * (len(row) - 1) / 2
        for i, v in enumerate(row):
            out[v] = (x0 + gap * i, y)
    return out


def rings_layout(levels, gap=1.5, start=90):
    """Concentric rings, one per level (BFS levels from `bfs_levels`): a level with
    one vertex sits at the center, the rest go around rings `gap` apart."""
    out = {}
    ring = 0
    for k, level in enumerate(levels):
        level = list(level)
        if k == 0 and len(level) == 1:
            out[level[0]] = (0.0, 0.0)
            continue
        ring += 1
        offset = 180 / len(level) if ring % 2 == 0 else 0  # stagger alternate rings
        out.update(circle_layout(level, radius=gap * ring, start=start + offset))
    return out


def flipped(layout):
    """The same layout upside down (for "the house graph, upside down")."""
    return {v: (x, -y) for v, (x, y) in layout.items()}


HOUSE_ADJ = {"a": ["b", "c"], "b": ["a", "c", "d"], "c": ["a", "b", "e"], "d": ["b", "e"], "e": ["c", "d"]}
HOUSE_LAYOUT = {"a": (0, 2.0), "b": (-1.1, 0.8), "c": (1.1, 0.8), "d": (-1.1, -1.2), "e": (1.1, -1.2)}
HOUSE_WEIGHTS = {("a", "b"): 4, ("a", "c"): 3, ("b", "c"): 2, ("b", "d"): 5, ("c", "e"): 1, ("d", "e"): 6}
DIRECTED_HOUSE = {"a": ["b"], "b": ["c", "d"], "c": ["a"], "d": ["e"], "e": ["c"]}

# Petersen vertices are the 2-element subsets of {1..5}, adjacent when disjoint
# (the Kneser graph K(5,2)), so both drawings, the edge list, and "S_ab ~ S_cd"
# all use the same names. PETERSEN_NUMBERS relabels them 0-9: outer pentagon 0-4,
# inner star 5-9, spoke i to i+5.
_P_OUTER = ["12", "34", "15", "23", "45"]
_P_INNER = ["35", "25", "24", "14", "13"]
PETERSEN_NUMBERS = {v: str(i) for i, v in enumerate(_P_OUTER + _P_INNER)}
PETERSEN_STAR_LAYOUT = {**circle_layout(_P_OUTER, radius=2.2), **circle_layout(_P_INNER, radius=1.1)}
# a 9-cycle around a center vertex, with the center's neighbors every third spot:
# 3-fold rotational symmetry
_P_CYCLE = ["34", "15", "23", "45", "13", "24", "35", "14", "25"]
PETERSEN_CIRCLE_LAYOUT = {"12": (0.0, 0.0), **circle_layout(_P_CYCLE, radius=2.2)}


def _bulge_out(layout, edges, angle=0.9):
    """Bends that curve each edge away from the origin (chords that would pass
    through the center vertex)."""
    bends = {}
    for u, v in edges:
        (ux, uy), (vx, vy) = layout[u][:2], layout[v][:2]
        left = (vx - ux) * (0 - uy) - (vy - uy) * (0 - ux) > 0  # origin left of u->v
        bends[(u, v)] = angle if left else -angle
    return bends


# the circle drawing's three chords pass right by the center vertex: curve them out
PETERSEN_CIRCLE_BENDS = _bulge_out(PETERSEN_CIRCLE_LAYOUT, [("15", "24"), ("23", "14"), ("13", "25")])


# ---------------------------------------------------------------------------
# Small algorithms the lectures animate
# ---------------------------------------------------------------------------

def bfs_levels(adj, start):
    """[[start], [its neighbors], [their new neighbors], ...]: the rings a highlight
    ripples through."""
    adj = parse_adj(adj)
    seen, levels = {start}, [[start]]
    while True:
        nxt = []
        for v in levels[-1]:
            for u in adj.get(v, []):
                if u not in seen:
                    seen.add(u)
                    nxt.append(u)
        if not nxt:
            return levels
        levels.append(nxt)


def kruskal(vertices, weights):
    """The steps of Kruskal's algorithm: [(u, v, w, kept), ...] in sorted order,
    stopping once the tree has V - 1 edges. `weights` is {(u, v): w}."""
    parent = {v: v for v in vertices}

    def root(v):
        while parent[v] != v:
            v = parent[v]
        return v

    steps, kept = [], 0
    for (u, v), w in sorted(weights.items(), key=lambda e: e[1]):
        if kept == len(parent) - 1:
            break
        ru, rv = root(u), root(v)
        ok = ru != rv
        if ok:
            parent[ru] = rv
            kept += 1
        steps.append((u, v, w, ok))
    return steps


# ---------------------------------------------------------------------------
# DrawnGraph
# ---------------------------------------------------------------------------

class DrawnGraph(GraphView):
    """A GraphView with graph-theory moves: highlight vertices and edges, walk a
    path, ripple out by levels, hide edges, and slide into another layout."""

    def __init__(self, positions, edges, adj=None, **kwargs):
        positions = {v: (p[0], p[1], 0) for v, p in positions.items()}  # layouts are 2D
        super().__init__(positions, edges, **kwargs)
        self.order = list(positions)
        self.layout0 = positions  # for morph_to: the scale the layout was drawn at
        # neighborhoods in the order the script gave them (for AdjacencyList)
        self.adj = parse_adj(adj) if adj is not None else None
        # What's marked, for describe(): kept as keys, updated when a method is called.
        self.lit_vertices, self.lit_edges, self.hidden = [], [], []
        self.groups, self.walked = [], None

    def describe(self):
        """GraphView's description, plus what's highlighted, walked, colored in groups,
        or hidden."""
        out = [super().describe()]
        edge = lambda e: f"{self.say(e[0])} {'to' if self.directed else 'and'} {self.say(e[1])}"
        if self.lit_vertices:
            out.append(f"Highlighted {'vertex' if len(self.lit_vertices) == 1 else 'vertices'}: "
                       f"{words(self.say(v) for v in self.lit_vertices)}.")
        if self.lit_edges:
            out.append(f"Highlighted {'edge' if len(self.lit_edges) == 1 else 'edges'}: "
                       f"{'; '.join(edge(e) for e in self.lit_edges)}.")
        if self.walked:
            out.append(f"Walk traced: {', '.join(self.say(v) for v in self.walked)}.")
        if self.groups:
            out.append(f"Colored in {count(len(self.groups), 'group')}: "
                       f"{'; '.join(words(self.say(v) for v in g) for g in self.groups)}.")
        if self.hidden:
            out.append(f"Hidden {'edge' if len(self.hidden) == 1 else 'edges'}: "
                       f"{'; '.join(edge(e) for e in self.hidden)}.")
        return " ".join(out)

    def _mark(self, marked, items, on):
        for x in items:
            if x is None:  # an edge the graph doesn't have
                continue
            if on and x not in marked:
                marked.append(x)
            elif not on and x in marked:
                marked.remove(x)

    # ---------- highlighting ----------

    def light(self, vertices=(), edges=(), color=None):
        """Highlight vertices (filled) and edges (colored, thicker), together."""
        color = color or T.focus
        self._mark(self.lit_vertices, vertices, True)
        self._mark(self.lit_edges, [self._key(u, v) for u, v in edges], True)
        anims = [self.fill(v, color) for v in vertices]
        anims += [self.color_edge(u, v, color) for u, v in edges]
        return AnimationGroup(*anims)

    def unlight(self, vertices=(), edges=()):
        self._mark(self.lit_vertices, list(vertices), False)
        self._mark(self.lit_edges, [self._key(u, v) for u, v in edges], False)
        anims = [self.fill(v, T.background, label_color=T.text) for v in vertices]
        anims += [self.color_edge(u, v, T.text) for u, v in edges]
        return AnimationGroup(*anims)

    def unlight_all(self):
        """Every vertex and edge back to plain (rings stay; see all_rings_off)."""
        self.groups, self.walked = [], None
        return self.unlight(self.vertices, self.edges)

    def light_path(self, vertices, color=None):
        """Highlight a path or cycle given as a vertex sequence ("abde" or a list):
        its vertices and the edges between consecutive ones."""
        vs = list(vertices)
        return self.light(vs, list(zip(vs, vs[1:])), color)

    def light_neighborhood(self, v, color=None, with_edges=False):
        """N(v) highlighted; `with_edges` also lights the edges out of v (degree)."""
        ns = self.neighbors(v)
        return self.light(ns, [(v, u) for u in ns] if with_edges else (), color)

    def paint(self, groups, colors=None):
        """Color vertex groups with different colors (a two-coloring, say). Colors
        default to the theme's palette, which has no other meaning."""
        colors = colors or T.palette
        self.groups = [list(g) for g in groups]
        return AnimationGroup(*[self.fill(v, colors[i % len(colors)])
                                for i, group in enumerate(groups) for v in group])

    # ---------- motion ----------

    def walk(self, vertices, color=None, trail=True, step_time=0.6):
        """A ring travels the walk one edge at a time ("bacbdec" or a list). With
        `trail`, each edge it crosses stays colored, so repeats show up as edges
        crossed twice. Returns one animation; the ring stays at the end (remove it
        with `all_rings_off()`)."""
        color = color or T.current
        vs = list(vertices)
        self.walked = vs
        steps = [self.ring(vs[0], color, key="walk")]
        for a, b in zip(vs, vs[1:]):
            step = [self.move_ring(a, b, key="walk")]
            if trail:
                step.append(self.color_edge(a, b, color))
            steps.append(AnimationGroup(*step, run_time=step_time))
        return Succession(*steps)

    def ripple(self, levels, color=None, keep=False, step_time=0.8):
        """A highlight spreads outward level by level (levels from `bfs_levels`):
        light level 0, then streak along each edge to the next level and light it.
        Without `keep`, a level goes dark as the highlight moves past it."""
        color = color or T.focus
        steps = [self.light(levels[0], color=color)]
        for prev, nxt in zip(levels, levels[1:]):
            streaks = [self.flash_edge(u, v, color=color) for u in prev for v in nxt if self.has_edge(u, v)]
            steps.append(AnimationGroup(*streaks, run_time=step_time))
            move = [self.light(nxt, color=color)]
            if not keep:
                move.append(self.unlight(prev))
            steps.append(AnimationGroup(*move))
        return Succession(*steps)

    def hide_edges(self, edges):
        """Fade edges out (a graph falling apart); `show_edges` brings them back."""
        self._mark(self.hidden, [self._key(u, v) for u, v in edges], True)
        return AnimationGroup(*[self.edge(u, v).animate.set_edge_opacity(0) for u, v in edges])

    def show_edges(self, edges):
        self._mark(self.hidden, [self._key(u, v) for u, v in edges], False)
        return AnimationGroup(*[self.edge(u, v).animate.set_edge_opacity(1) for u, v in edges])

    def morph_to(self, layout, scale=None, **kwargs):
        """Slide every vertex to its spot in another layout (an isomorphism, a
        redrawing); edges follow. The new layout is drawn at the same scale as the
        one the graph was built with (vertices stay as far apart as they were) and
        centered where the graph is now. `scale` multiplies that, e.g. 0.8 if the
        new layout is bigger than the room on the slide. `bends` {(u, v): angle}
        curves edges on the way (the Petersen circle needs PETERSEN_CIRCLE_BENDS)."""
        now = np.array([self.center_of(v) for v in layout])
        new = np.array([[p[0], p[1], 0.0] for p in layout.values()])
        k = self._drawn_scale() * (scale or 1.0)
        mid_now = (now.max(axis=0) + now.min(axis=0)) / 2
        mid_new = (new.max(axis=0) + new.min(axis=0)) / 2
        targets = {v: mid_now + (p - mid_new) * k for v, p in zip(layout, new)}
        return self.move_to_layout(targets, **kwargs)

    def _drawn_scale(self):
        """How much the graph has been scaled since it was built from its layout."""
        vs = self.order
        best = 0, 1.0
        for i, u in enumerate(vs):  # the farthest-apart pair measures it best
            for v in vs[i + 1:]:
                d0 = np.linalg.norm(np.array(self.layout0[u]) - np.array(self.layout0[v]))
                if d0 > best[0]:
                    best = d0, np.linalg.norm(self.center_of(u) - self.center_of(v)) / d0
        return best[1]


# ---------------------------------------------------------------------------
# Building graphs
# ---------------------------------------------------------------------------

def graph_from(vertices, edges, layout=None, **kwargs):
    """`Graph[V, E]`: vertices and edge pairs, drawn around a circle unless a layout
    ({vertex: (x, y)}) is given. kwargs go to GraphView (directed, weights, labels,
    dots_only, radius, font_size, ...)."""
    vertices = [str(v) for v in vertices]
    edges = [(str(u), str(v)) for u, v in edges]
    return DrawnGraph(layout or circle_layout(vertices), edges, **kwargs)


def adj_graph(adj, layout=None, directed=False, **kwargs):
    """`AdjGraph{a : [b,c], ...}` (the text or a dict). For a directed graph each
    list is the out-neighbors."""
    adj = parse_adj(adj)
    vertices = list(adj)
    for us in adj.values():
        vertices += [u for u in us if u not in vertices]
    return DrawnGraph(layout or circle_layout(vertices), adj_edges(adj, directed),
                      adj=adj, directed=directed, **kwargs)


def _names(n):
    return [str(i) for i in range(n)]


def empty(n, **kwargs):
    """E_n: n vertices around a circle, no edges. Vertices are "0".."n-1"."""
    return graph_from(_names(n), [], **kwargs)


def complete(n, **kwargs):
    """K_n around a circle."""
    vs = _names(n)
    return graph_from(vs, [(vs[i], vs[j]) for i in range(n) for j in range(i + 1, n)], **kwargs)


def cycle(n, **kwargs):
    """C_n around a circle."""
    vs = _names(n)
    return graph_from(vs, [(vs[i], vs[(i + 1) % n]) for i in range(n)], **kwargs)


def path(n, **kwargs):
    """P_n: n vertices in a row."""
    vs = _names(n)
    kwargs.setdefault("layout", line_layout(vs))
    return graph_from(vs, list(zip(vs, vs[1:])), **kwargs)


def cube(n, **kwargs):
    """Q_n as a cube drawing; vertices are bit strings, adjacent when they differ
    in one bit. Bit-string labels get small past Q_3: pass dots_only=True."""
    layout = cube_layout(n)
    vs = list(layout)
    edges = [(u, v) for i, u in enumerate(vs) for v in vs[i + 1:]
             if sum(a != b for a, b in zip(u, v)) == 1]
    kwargs.setdefault("layout", layout)
    return graph_from(vs, edges, **kwargs)


def bipartite(top, bottom, edges=None, **kwargs):
    """Two rows of vertices; every top-bottom pair is an edge unless `edges` says
    otherwise (so `bipartite("ace", "bdf")` is K_{3,3})."""
    top, bottom = [str(v) for v in top], [str(v) for v in bottom]
    if edges is None:
        edges = [(u, v) for u in top for v in bottom]
    kwargs.setdefault("layout", bipartite_layout(top, bottom))
    return graph_from(top + bottom, edges, **kwargs)


def house(weighted=False, directed=False, **kwargs):
    """The house graph: triangle a, b, c on top of the square b, c, d, e.
    `weighted` uses HOUSE_WEIGHTS; `directed` uses DIRECTED_HOUSE."""
    adj = DIRECTED_HOUSE if directed else HOUSE_ADJ
    if weighted:
        kwargs.setdefault("weights", HOUSE_WEIGHTS)
    kwargs.setdefault("layout", HOUSE_LAYOUT)
    return adj_graph(adj, directed=directed, **kwargs)


def petersen(drawing="star", numbers=False, **kwargs):
    """The Petersen graph, drawn as "star" (pentagram in a pentagon) or "circle"
    (a 9-cycle around a center vertex). Vertices are named by the 2-element subsets
    of {1..5} ("12", "34", ...) in both drawings, so `morph_to` turns one into the
    other: `g.morph_to(PETERSEN_CIRCLE_LAYOUT, bends=PETERSEN_CIRCLE_BENDS)`.
    `numbers=True` shows the labels 0-9 instead (outer 0-4, inner 5-9)."""
    layout = {"star": PETERSEN_STAR_LAYOUT, "circle": PETERSEN_CIRCLE_LAYOUT}[drawing]
    vs = _P_OUTER + _P_INNER
    edges = [(u, v) for i, u in enumerate(vs) for v in vs[i + 1:] if not set(u) & set(v)]
    if numbers:
        kwargs.setdefault("labels", PETERSEN_NUMBERS)
    if drawing == "circle":
        kwargs.setdefault("bends", PETERSEN_CIRCLE_BENDS)
    return graph_from(vs, edges, layout=dict(layout), **kwargs)


# ---------------------------------------------------------------------------
# Representations
# ---------------------------------------------------------------------------

def _cell(text, w, h, font_size):
    box = Rectangle(width=w, height=h, stroke_width=2, color=T.text)
    t = mono(str(text), font_size=font_size)
    if t.width > w - 0.1:
        t.scale_to_fit_width(w - 0.1)
    t.move_to(box)
    return VGroup(box, t)


def _fmt(w):
    return str(int(w)) if float(w).is_integer() else str(w)


class AdjacencyMatrix(AltText, VGroup):
    """A grid of cells with the vertex names along the top and left. Cells are
    addressed by vertex name or index: `m.cell("a", "b")`, `m.cell(0, 1)`.

        m = AdjacencyMatrix.from_graph(g)                 # 0/1, or weights if g has them
        m = AdjacencyMatrix(parse_matrix(SCRIPT_TEXT))    # rows straight from a script
        self.play(m.light_row("b"))                       # loop through N(b)
    """

    def __init__(self, rows, names=None, cell=0.6, font_size=24, show_names=True):
        super().__init__()
        n = len(rows)
        self.names = [str(v) for v in (names or range(n))]
        self.index = {v: i for i, v in enumerate(self.names)}
        self.rows = [[str(x) for x in row] for row in rows]  # as text, for describe()
        self.cells = VGroup()
        self.grid = []
        for i, row in enumerate(rows):
            line = []
            for j, val in enumerate(row):
                c = _cell(val, cell, cell, font_size).move_to([j * cell, -i * cell, 0])
                self.cells.add(c)
                line.append(c)
            self.grid.append(line)
        self.add(self.cells)
        self.row_names = VGroup()
        self.col_names = VGroup()
        if show_names:
            for i, v in enumerate(self.names):
                self.row_names.add(mono(v, font_size=font_size, color=T.label)
                                   .move_to([-cell * 0.85, -i * cell, 0]))
                self.col_names.add(mono(v, font_size=font_size, color=T.label)
                                   .move_to([i * cell, cell * 0.85, 0]))
            self.add(self.row_names, self.col_names)

    @classmethod
    def from_graph(cls, g, order=None, weighted=None, missing=None, **kwargs):
        """The matrix of a DrawnGraph/GraphView, vertices in `order` (default: the
        graph's own order). Weighted graphs show weights, with `missing` (default
        "-") where there's no edge; unweighted show 1 and 0."""
        order = [str(v) for v in (order or list(g.vertices))]
        weighted = bool(g.weights) if weighted is None else weighted
        missing = missing if missing is not None else ("-" if weighted else "0")
        rows = []
        for u in order:
            row = []
            for v in order:
                key = (u, v) if g.directed else g._key(u, v)
                if key is None or key not in g.edges:
                    row.append(missing)
                elif weighted:
                    row.append(_fmt(g.weights[key]))
                else:
                    row.append("1")
            rows.append(row)
        return cls(rows, names=order, **kwargs)

    def describe(self):
        out = [f"An adjacency matrix. Rows and columns are {words(self.names)}."]
        out += [f"Row {name}: {', '.join(row)}." for name, row in zip(self.names, self.rows)]
        return " ".join(out)

    def _i(self, v):
        return v if isinstance(v, int) else self.index[str(v)]

    def cell(self, u, v):
        return self.grid[self._i(u)][self._i(v)]

    def row(self, u):
        return VGroup(*self.grid[self._i(u)])

    def light(self, u, v, color=None, opacity=0.4):
        """Highlight one cell's background (STYLE.md: cells highlight by background)."""
        return self.cell(u, v)[0].animate.set_fill(color or T.focus, opacity=opacity)

    def light_row(self, u, color=None, opacity=0.4):
        return AnimationGroup(*[c[0].animate.set_fill(color or T.focus, opacity=opacity)
                                for c in self.grid[self._i(u)]])

    def light_col(self, v, color=None, opacity=0.4):
        j = self._i(v)
        return AnimationGroup(*[r[j][0].animate.set_fill(color or T.focus, opacity=opacity) for r in self.grid])

    def unlight_all(self):
        return AnimationGroup(*[c[0].animate.set_fill(opacity=0) for c in self.cells])


class AdjacencyList(AltText, VGroup):
    """One row per vertex: its name, an arrow, and a cell per neighbor, in order.

        l = AdjacencyList(parse_adj("{a : [b,c], b : [a,c]}"))
        l = AdjacencyList.from_graph(g)      # weighted graphs show "b 4" cells
        self.play(l.light_row("b"), l.light("b", "d", T.good))
    """

    def __init__(self, adj, weights=None, order=None, cell_h=0.55, font_size=24, gap=0.18):
        super().__init__()
        adj = parse_adj(adj)
        self.order = [str(v) for v in (order or list(adj))]
        weights = weights or {}
        self.heads, self.entries, self.rows_ = {}, {}, {}
        self.texts = {}  # vertex -> its entries as text, for describe()
        name_w = max(mono(v, font_size=font_size).width for v in self.order) + 0.3
        y = 0.0
        for v in self.order:
            head = _cell(v, name_w, cell_h, font_size)
            head[1].set_color(T.label)
            head.move_to([name_w / 2, y, 0])
            arrow = Arrow(head.get_right(), head.get_right() + RIGHT * 0.7, buff=0.05,
                          stroke_width=3, color=T.text, max_tip_length_to_length_ratio=0.3)
            row = VGroup(head, arrow)
            x = arrow.get_right()[0] + 0.05
            for u in adj.get(v, []):
                w = weights.get((v, u), weights.get((u, v)))
                text = u if w is None else f"{u} {_fmt(w)}"
                width = max(cell_h, mono(text, font_size=font_size).width + 0.25)
                c = _cell(text, width, cell_h, font_size).move_to([x + width / 2, y, 0])
                x += width
                self.entries[(v, u)] = c
                self.texts.setdefault(v, []).append(text)
                row.add(c)
            self.heads[v] = head
            self.rows_[v] = row
            self.add(row)
            y -= cell_h + gap

    @classmethod
    def from_graph(cls, g, order=None, **kwargs):
        """A DrawnGraph's neighborhoods: the script's order if it was built from an
        AdjGraph, edge order otherwise. Shows weights if the graph has them."""
        adj = getattr(g, "adj", None) or {v: g.neighbors(v) for v in g.vertices}
        return cls(adj, weights=g.weights or None, order=order, **kwargs)

    def describe(self):
        rows = [f"{v}: {', '.join(self.texts[v]) if self.texts.get(v) else 'no neighbors'}" for v in self.order]
        return f"An adjacency list. {'. '.join(rows)}."

    def entry(self, v, u):
        return self.entries[(str(v), str(u))]

    def row(self, v):
        return self.rows_[str(v)]

    def light(self, v, u, color=None, opacity=0.4):
        return self.entry(v, u)[0].animate.set_fill(color or T.focus, opacity=opacity)

    def light_row(self, v, color=None, opacity=0.4):
        """The head and every entry of v's row: looping through N(v)."""
        cells = [self.heads[str(v)]] + [c for (a, _), c in self.entries.items() if a == str(v)]
        return AnimationGroup(*[c[0].animate.set_fill(color or T.focus, opacity=opacity) for c in cells])

    def unlight_all(self):
        cells = list(self.heads.values()) + list(self.entries.values())
        return AnimationGroup(*[c[0].animate.set_fill(opacity=0) for c in cells])


class EdgeList(AltText, VGroup):
    """A column of edges, one cell each ("a-b" or "a-b 4"), that can be sorted by
    weight and marked kept/rejected, for Kruskal's algorithm.

        el = EdgeList.from_graph(g).next_to(g, RIGHT)
        self.play(el.gather_from(g))          # each edge lights up and moves over
        self.play(el.sort_by_weight())        # cells slide into sorted order
        for u, v, w, ok in kruskal(g.vertices, g.weights):
            self.play(el.light(u, v), g.light(edges=[(u, v)]))
            self.play(el.mark(u, v, ok), g.color_edge(u, v, T.good if ok else T.bad))
    """

    def __init__(self, edges, weights=None, directed=False, font_size=24, cell_h=0.55, gap=0.1,
                 pairs=False):
        super().__init__()
        weights = weights or {}
        self.directed = directed
        self.items = {}
        self.weights = {}
        self.marks = {}
        self.kept = {}  # edge -> True (kept) / False (rejected), for describe()
        sep = "->" if directed else "-"
        texts = []
        for u, v in edges:
            w = weights.get((u, v), weights.get((v, u)))
            name = f"({u},{v})" if pairs else f"{u}{sep}{v}"
            texts.append(((u, v), name if w is None else f"{name} {_fmt(w)}", w))
        width = max(mono(t, font_size=font_size).width for _, t, _ in texts) + 0.35 if texts else 1
        for i, (key, text, w) in enumerate(texts):
            c = _cell(text, width, cell_h, font_size).move_to([0, -i * (cell_h + gap), 0])
            self.items[key] = c
            self.weights[key] = w
            self.add(c)
        self.order = [k for k, _, _ in texts]

    @classmethod
    def from_graph(cls, g, **kwargs):
        return cls(list(g.edges), weights=g.weights or None, directed=g.directed, **kwargs)

    def describe(self):
        def say(k):
            u, v = k
            w = self.weights[k]
            out = f"{u} {'to' if self.directed else 'and'} {v}" + (f", weight {_fmt(w)}" if w is not None else "")
            if k in self.kept:
                out += ", kept" if self.kept[k] else ", rejected"
            return out
        return f"A list of {count(len(self.order), 'edge')}: {'; '.join(say(k) for k in self.order)}."

    def _key(self, u, v):
        if (u, v) in self.items:
            return (u, v)
        if not self.directed and (v, u) in self.items:
            return (v, u)
        raise KeyError(f"no edge {u}-{v}")

    def item(self, u, v):
        return self.items[self._key(u, v)]

    def gather_from(self, g, step_time=0.5):
        """Each edge lights up in the graph and a copy of it moves into its cell.
        The list isn't on screen before this; this brings it in."""
        steps = []
        for key in self.order:
            c = self.items[key]
            e = g.edge(*key)
            steps.append(AnimationGroup(g.color_edge(*key, T.focus), run_time=step_time * 0.6))
            steps.append(AnimationGroup(TransformFromCopy(e.line, c[0]), FadeIn(c[1]),
                                        g.color_edge(*key, T.text), run_time=step_time))
        return Succession(*steps)

    def sort_by_weight(self):
        """Every cell slides to its place in sorted order (ties keep their order)."""
        slots = [self.items[k].get_center().copy() for k in self.order]  # where the list is now
        new = sorted(self.order, key=lambda k: self.weights[k] if self.weights[k] is not None else 0)
        anims = [self.items[k].animate.move_to(slots[i]) for i, k in enumerate(new)]
        self.order = new
        return AnimationGroup(*anims)

    def light(self, u, v, color=None, opacity=0.4):
        return self.item(u, v)[0].animate.set_fill(color or T.focus, opacity=opacity)

    def mark(self, u, v, ok, opacity=0.4):
        """Kept (good, with a check) or rejected (bad, with an X). STYLE.md: never
        color alone."""
        c = self.item(u, v)
        color = T.good if ok else T.bad
        sym = Text("✓" if ok else "✗", font_size=28, color=color).next_to(c, RIGHT, buff=0.15)
        self.marks[self._key(u, v)] = sym
        self.kept[self._key(u, v)] = ok
        self.add(sym)
        return AnimationGroup(c[0].animate.set_fill(color, opacity=opacity), FadeIn(sym))

    def unlight_all(self):
        anims = [c[0].animate.set_fill(opacity=0) for c in self.items.values()]
        anims += [FadeOut(m) for m in self.marks.values()]
        self.remove(*self.marks.values())
        self.marks = {}
        self.kept = {}
        return AnimationGroup(*anims) if anims else Wait(0)
