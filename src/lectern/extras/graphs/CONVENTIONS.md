# Graphs conventions

Script directives for graph theory: naming and drawing graphs, highlighting them,
and showing their representations. Everything here is in `__init__.py`:

```python
from lectern.extras.graphs import *
```

Search algorithms (DFS/BFS WHITE/GRAY/BLACK coloring, `.gr` files) use `GraphView`
in `lectern.structures.graph`. Every graph built here is a `DrawnGraph`, which is a
`GraphView`, so those methods work too.

## Writing a graph

```
Graph[[a,b,c], [(a,b),(b,c)]]
AdjGraph{a : [b,c], b : [a,c], c : [a,b]}
```

- `Graph[V, E]`: a list of vertices and a list of edge pairs.
  In code: `graph_from(*parse_graph(text))`, or `graph_from(["a","b"], [("a","b")])`.
- `AdjGraph{...}`: neighborhoods in Python dictionary syntax. The order of each list
  is the order a loop over that neighborhood visits it, and `AdjacencyList` shows it
  in that order. In code: `adj_graph(text)` (the script text, or a dict). For a
  directed graph each list is the out-neighbors: `adj_graph(text, directed=True)`.
- Unless the script says how to draw it, vertices go evenly around a circle. Pass
  `layout={v: (x, y)}` (or one of the layouts below) to place them.

## Named graphs

| script         | code                     | drawn as                                     |
|----------------|--------------------------|----------------------------------------------|
| `E_n`          | `empty(n)`               | n vertices around a circle, no edges         |
| `K_n`          | `complete(n)`            | around a circle                              |
| `C_n`          | `cycle(n)`               | around a circle                              |
| `P_n`          | `path(n)`                | n vertices in a row                          |
| `Q_n`          | `cube(n)`                | the n-dimensional cube; vertices are bit strings |
| `K_{m,n}`      | `bipartite("abc", "de")` | two rows, every edge between them            |
| house          | `house()`                | triangle a, b, c on the square b, c, d, e    |
| weighted house | `house(weighted=True)`   | `HOUSE_WEIGHTS`                              |
| directed house | `house(directed=True)`   | `DIRECTED_HOUSE`                             |
| petersenStar   | `petersen("star")`       | pentagram inside a pentagon                  |
| petersenCircle | `petersen("circle")`     | a 9-cycle around a center vertex, 3-fold symmetric |

Numbered graphs name their vertices `"0"` to `"n-1"`, like the Python on the slides.
Petersen vertices are named by the 2-element subsets of {1..5} (`"12"`, `"34"`, ...),
adjacent when disjoint, in both drawings, so one drawing can morph into the other.
`petersen(..., numbers=True)` shows 0-9 instead (outer 0-4, inner 5-9, spoke i to i+5).

Bit-string labels get small past `Q_3`; pass `dots_only=True` for bigger cubes.

## Highlighting

Same rules as STYLE.md: highlight by fill, never by color alone when it matters.

- A highlighted vertex is filled (`T.focus` unless the script says otherwise); a
  highlighted edge is colored and thicker. `g.light(vertices, edges)`,
  `g.unlight(...)`, `g.unlight_all()`.
- "highlight the path/cycle a, b, d, e": `g.light_path("abde")`.
- "highlight the neighborhood of b": `g.light_neighborhood("b")`;
  with the edges out of b (its degree): `with_edges=True`.
- Coloring vertices into groups (a two-coloring) uses the theme palette, which has
  no other meaning: `g.paint([["b", "e"], ["c", "d"]])`.

## Motion

- "walk from b, a, c, b, ...": a ring (`T.current`) travels edge by edge and leaves
  the edges it crossed colored, so a repeat shows as an edge crossed twice:
  `g.walk("bacbdec")`. Remove the ring with `g.all_rings_off()`.
- "ripple outward" / "move the highlight out to the neighbors": `g.ripple(levels)`
  with `levels = bfs_levels(adj, start)`. Streaks run along the edges to the next
  level, which lights up; the previous level goes dark unless `keep=True`.
- "fade out the edges ...": `g.hide_edges([...])`, `g.show_edges([...])`.
- "redraw it as ...", "turn one into the other", isomorphisms: `g.morph_to(layout)`.
  Vertices slide, edges follow, nothing is rebuilt. The new layout keeps the
  graph's current scale; pass `scale=` if it needs to shrink to fit.
  Petersen star to circle: `g.morph_to(PETERSEN_CIRCLE_LAYOUT, bends=PETERSEN_CIRCLE_BENDS)`.

## Layouts

`{vertex: (x, y)}` dicts, about 4 units across, all at the same scale (vertices
about 1.3 apart), so morphing between them keeps vertices the same distance apart.

- `circle_layout(vs)`, `line_layout(vs)`, `cube_layout(n)`
- `bipartite_layout(top, bottom)`: two rows
- `rings_layout(levels)`: concentric rings, one per BFS level, the start at the center
- `flipped(layout)`: upside down ("the house graph upside down")
- `HOUSE_LAYOUT`, `PETERSEN_STAR_LAYOUT`, `PETERSEN_CIRCLE_LAYOUT`

## Representations

```
draw the matrix
0 & 1 & 1 \\
1 & 0 & 1 \\
1 & 1 & 0 \\
```

- Adjacency matrix: `AdjacencyMatrix.from_graph(g)` (0/1, or weights with `-` for
  no edge), or the script's rows: `AdjacencyMatrix(parse_matrix(text), names=...)`.
  Rows and columns are labeled with vertex names. `m.light(u, v)`,
  `m.light_row(u)` (looping through N(u)), `m.light_col(v)`, `m.unlight_all()`.
- Adjacency list: `AdjacencyList.from_graph(g)` or `AdjacencyList(adj)`. Weighted
  entries read `b 4`. `l.light(v, u)`, `l.light_row(v)`, `l.unlight_all()`.
- Edge list: `EdgeList.from_graph(g)`, one cell per edge (`a-b`, `a->b` directed,
  `pairs=True` for `(a,b)`). `el.gather_from(g)` brings the list in by moving each
  edge out of the graph; `el.sort_by_weight()` slides the cells into sorted order;
  `el.mark(u, v, ok)` marks a cell kept (good, ✓) or rejected (bad, ✗).

Highlighting a vertex in the graph and its row in a representation at the same
time is one `self.play(...)`: every method returns an animation.

## Algorithms

Plain helpers that compute what to animate:

- `bfs_levels(adj, start)`: the levels a ripple goes through.
- `kruskal(vertices, weights)`: `[(u, v, w, kept), ...]` in sorted order, stopping
  at V - 1 edges. Drive the edge list and the graph with it:

```python
for u, v, w, ok in kruskal(g.vertices, g.weights):
    self.play(el.light(u, v), g.light(edges=[(u, v)]))
    self.play(el.mark(u, v, ok), g.color_edge(u, v, T.good if ok else T.bad))
```

## Alt text

A graph's automatic alt text lists every vertex and edge, then whatever is
highlighted, walked, colored in groups, or hidden. That's complete but long. Give
every graph its own `alt:` line (or `.with_alt(...)`) saying what the graph is for,
in the script's words: "the house graph", "K_4, every pair of vertices joined". When
the slide's point is something highlighted (a cycle, a walk, a neighborhood), say
which vertices and edges, since the narration will refer to them.

The representations describe themselves fully (matrix row by row, list vertex by
vertex, edge list in its current order with kept/rejected marks); keep those unless
the slide only uses part of one.
