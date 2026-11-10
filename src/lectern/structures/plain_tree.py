"""Plain tree visual for Manim -- the `tree[...]` form in SCRIPT_CONVENTIONS.md.

Draws only node labels and plain lines between them (no boxes, no pointer
slots, no arrowheads), for trees with any number of children per node
(expression trees, directory trees, ternary/rose trees, tries, heaps, ...).
Compare `structures.tree.Tree`, the boxed pointer-diagram form for binary trees.

Layout: leaves (and `_` placeholders) get consecutive x-slots left to right,
spaced by their own label widths plus `sibling_gap`; each internal node sits
centered over its first and last child (so an only child is straight below);
depth sets y. The finished tree is centered on ORIGIN -- move it afterwards
like any other mobject. Edge endpoints are computed once, at construction,
from each node's layout position, and stop short of both labels.

Each node carries an invisible rounded "highlight" background behind its
label, so nodes can be highlighted like the other structures' cells. Every
node and every edge is individually addressable: `find(label)` / `node_at(path)`
return a `PlainTreeNode`, and `node.edge` is the line from its parent.
Mutating methods return Animations rather than playing them.
"""

from typing import List, Optional
from manim import *
import numpy as np

from lectern.structures.tree import _rect_boundary_point
from lectern.structures.tree_spec import parse_tree_spec
from lectern.theme import T
from lectern.alt import AltText, count, describe_tree, words


class PlainTreeNode(VGroup):
    def __init__(self, value, font_size=30, color=None, pad=0.14):
        color = T.text if color is None else color
        super().__init__()
        self.value = value
        self.label = Text(str(value), font_size=font_size, color=color)
        width = max(self.label.width, self.label.height) + 2 * pad
        height = max(self.label.height + 2 * pad, 0.5 * font_size / 30)
        self.bg = RoundedRectangle(
            width=width, height=height, corner_radius=min(width, height) / 2,
            stroke_width=0, stroke_opacity=0, fill_opacity=0,
        )
        self.add(self.bg, self.label)
        self.children: List[Optional["PlainTreeNode"]] = []
        self.parent: Optional["PlainTreeNode"] = None
        self.edge: Optional[Line] = None
        self.path = ()

    @property
    def half_width(self):
        return self.bg.width / 2

    @property
    def half_height(self):
        return self.bg.height / 2


class PlainTree(AltText, VGroup):
    def __init__(self, spec, font_size=30, level_gap=1.0, sibling_gap=0.5, placeholder_width=0.5,
                 color=None, edge_color=None, edge_width=2, edge_buff=0.05):
        color = T.text if color is None else color
        edge_color = T.text if edge_color is None else edge_color
        super().__init__()
        self.font_size = font_size
        self.level_gap = level_gap
        self.sibling_gap = sibling_gap
        self.placeholder_width = placeholder_width
        self.edge_color = edge_color
        self.edge_width = edge_width

        parsed = parse_tree_spec(spec) if isinstance(spec, str) else spec
        self.root = self._build(parsed, None, (), font_size, color)

        self._next_x = 0.0
        self._last_right = None
        self._layout(self.root, 0)

        self.edges = VGroup()
        for node in self.nodes():
            for child in node.children:
                if child is None:
                    continue
                direction = child.get_center() - node.get_center()
                start = _rect_boundary_point(node.get_center(), node.half_width + edge_buff,
                                             node.half_height + edge_buff, direction)
                end = _rect_boundary_point(child.get_center(), child.half_width + edge_buff,
                                           child.half_height + edge_buff, -direction)
                child.edge = Line(start, end, color=edge_color, stroke_width=edge_width)
                self.edges.add(child.edge)

        # Edges first so highlight backgrounds draw over line ends.
        self.add(self.edges, *self.nodes())
        self.move_to(ORIGIN)

    def describe(self):
        return "A tree. " + describe_tree(self.root, lambda n: n.children, lambda n: n.value)

    # ---------- construction ----------

    def _build(self, parsed, parent, path, font_size, color):
        label, children = parsed
        node = PlainTreeNode(label, font_size=font_size, color=color)
        node.parent = parent
        node.path = path
        for i, child in enumerate(children):
            if child is None:
                node.children.append(None)
            else:
                node.children.append(self._build(child, node, path + (i,), font_size, color))
        return node

    def _slot(self, width):
        """Next leaf-slot center x for something `width` wide."""
        if self._last_right is None:
            x = width / 2
        else:
            x = self._last_right + self.sibling_gap + width / 2
        self._last_right = x + width / 2
        return x

    def _layout(self, node, depth):
        """Returns this subtree's root x (placeholders return their slot x too)."""
        y = -depth * self.level_gap
        if node is None:
            return self._slot(self.placeholder_width)
        if not node.children:
            x = self._slot(node.bg.width)
        else:
            xs = [self._layout(child, depth + 1) for child in node.children]
            x = (xs[0] + xs[-1]) / 2
        node.move_to(np.array([x, y, 0.0]))
        return x

    # ---------- lookup ----------

    def nodes(self) -> List[PlainTreeNode]:
        """All nodes, preorder."""
        out = []

        def visit(node):
            if node is None:
                return
            out.append(node)
            for child in node.children:
                visit(child)

        visit(self.root)
        return out

    def find(self, label, occurrence=0) -> PlainTreeNode:
        matches = [n for n in self.nodes() if str(n.value) == str(label)]
        if len(matches) <= occurrence:
            raise KeyError(f"no node labelled {label!r} (occurrence {occurrence})")
        return matches[occurrence]

    def __getitem__(self, label) -> PlainTreeNode:
        return self.find(label)

    def node_at(self, path) -> PlainTreeNode:
        node = self.root
        for i in path:
            node = node.children[i]
        return node

    def subtree(self, node: PlainTreeNode, include_edge=False) -> VGroup:
        """`node`, all its descendants, and the edges among them (plus the edge
        into `node` itself if `include_edge`)."""
        group = VGroup()
        if include_edge and node.edge is not None:
            group.add(node.edge)

        def visit(n):
            group.add(n)
            for child in n.children:
                if child is not None:
                    group.add(child.edge)
                    visit(child)

        visit(node)
        return group

    def leaves(self) -> List[PlainTreeNode]:
        return [n for n in self.nodes() if not any(c is not None for c in n.children)]

    def depth(self) -> int:
        """Number of nodes on the longest root-to-leaf path."""
        def h(n):
            if n is None:
                return 0
            return 1 + max([h(c) for c in n.children] or [0])
        return h(self.root)

    # ---------- highlighting ----------

    def highlight_node(self, node: PlainTreeNode, color=None, opacity=0.35) -> Animation:
        color = T.focus if color is None else color
        return node.bg.animate.set_fill(color, opacity=opacity).set_stroke(color, width=2, opacity=1)

    def unhighlight_node(self, node: PlainTreeNode) -> Animation:
        return node.bg.animate.set_fill(opacity=0).set_stroke(opacity=0)

    def highlight_edge(self, child: PlainTreeNode, color=None, width=5) -> Animation:
        """Highlight the edge from `child`'s parent down to `child`."""
        color = T.focus if color is None else color
        return child.edge.animate.set_stroke(color, width=width)

    def unhighlight_edge(self, child: PlainTreeNode) -> Animation:
        return child.edge.animate.set_stroke(self.edge_color, width=self.edge_width)


__all__ = ["PlainTreeNode", "PlainTree"]
