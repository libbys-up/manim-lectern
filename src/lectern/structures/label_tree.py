"""`LabelTree`: a tree of text labels with no boxes around them, like a parse tree or
an abstract syntax tree.

    t = LabelTree("E [E [T id]] + [T id]")
    self.play(t.lit("+"))            # highlight a node by its label...
    self.play(t.lit(t.at(0, 0)))     # ...or by its path from the root
    self.play(FadeIn(t.subtree("T", occ=1)))

Nodes are found by label (the `occ`th node with that label, in preorder), by preorder
index, or with `at(*child_indices)`. A `~` in a label is drawn as a space.

Links between nodes are list indices, not references, so `.animate` is safe on any
part of the tree.
"""

from manim import DOWN, Line, RoundedRectangle, Text, VGroup, ORIGIN

from lectern.geometry import box_point
from lectern.structures.tree_spec import parse_tree_spec
from lectern.theme import T

__all__ = ["LabelTree"]


class LabelTree(VGroup):

    def __init__(self, spec, font_size=28, level_gap=0.95, sibling_gap=0.4, color=None):
        super().__init__()
        color = color or T.text
        parsed = parse_tree_spec(spec, placeholders=False) if isinstance(spec, str) else spec
        self.nodes_, self.parent_, self.kids_ = VGroup(), [], []
        self.labels_ = []
        self._right = None

        def build(p, parent):
            i = len(self.labels_)
            label = Text(p[0].replace("~", " "), font_size=font_size, color=color)
            w = max(label.width, label.height) + 0.26
            h = max(label.height + 0.26, 0.5 * font_size / 30)
            # An invisible pill behind each label; lit() fills it in.
            bg = RoundedRectangle(width=w, height=h, corner_radius=min(w, h) / 2,
                                  stroke_width=0, stroke_opacity=0, fill_opacity=0)
            self.nodes_.add(VGroup(bg, label))
            self.labels_.append(p[0])
            self.parent_.append(parent)
            self.kids_.append([])
            if parent is not None:
                self.kids_[parent].append(i)
            for k in p[1]:
                build(k, i)

        build(parsed, None)

        # Leaves go left to right; each parent is centered over its children.
        def place(i, depth):
            n = self.nodes_[i]
            if self.kids_[i]:
                xs = [place(k, depth + 1) for k in self.kids_[i]]
                x = (xs[0] + xs[-1]) / 2
            else:
                w = n[0].width
                x = w / 2 if self._right is None else self._right + sibling_gap + w / 2
                self._right = x + w / 2
            n.move_to([x, -depth * level_gap, 0])
            return x

        place(0, 0)
        self.edges_ = VGroup()
        self.edge_of = {}  # node index -> index in edges_ of the edge from its parent
        for i, par in enumerate(self.parent_):
            if par is None:
                continue
            a, b = self.nodes_[par], self.nodes_[i]
            d = b.get_center() - a.get_center()
            line = Line(box_point(a, d), box_point(b, -d), color=color, stroke_width=2)
            self.edge_of[i] = len(self.edges_)
            self.edges_.add(line)
        self.add(self.edges_, self.nodes_)
        self.move_to(ORIGIN)

    def idx(self, key, occ=0):
        """Preorder index of a node: `key` is an index already, or a label."""
        if isinstance(key, int):
            return key
        hits = [i for i, l in enumerate(self.labels_) if l == str(key)]
        return hits[occ]

    def n(self, key, occ=0):
        """The node (a VGroup of its background and label)."""
        return self.nodes_[self.idx(key, occ)]

    def at(self, *path):
        """Index of the node reached by following child indices from the root."""
        i = 0
        for p in path:
            i = self.kids_[i][p]
        return i

    def edge(self, key, occ=0):
        """The edge from a node's parent to the node."""
        return self.edges_[self.edge_of[self.idx(key, occ)]]

    def lit(self, key, color=None, occ=0, opacity=0.35):
        """Animation: highlight a node's background."""
        color = color or T.focus
        return self.n(key, occ)[0].animate.set_fill(color, opacity=opacity).set_stroke(color, width=2, opacity=1)

    def unlit(self, key, occ=0):
        return self.n(key, occ)[0].animate.set_fill(opacity=0).set_stroke(opacity=0)

    def subtree(self, key, occ=0):
        """A node, everything below it, and the edges between them."""
        out, stack = VGroup(), [self.idx(key, occ)]
        while stack:
            i = stack.pop()
            out.add(self.nodes_[i])
            for k in self.kids_[i]:
                out.add(self.edges_[self.edge_of[k]])
                stack.append(k)
        return out

    def tag(self, key, text, occ=0, color=None):
        """A small note under a node (an attribute value, a type)."""
        # The background keeps the tree's edges from running through the tag.
        return (Text(text, font_size=18, color=color or T.good).next_to(self.n(key, occ), DOWN, buff=0.02)
                .add_background_rectangle(T.background, opacity=1, buff=0.02))

    def preorder(self):
        return list(range(len(self.labels_)))
