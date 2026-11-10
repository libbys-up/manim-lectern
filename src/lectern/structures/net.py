"""`Net`: a graph whose vertices you place by hand, for state machines, control-flow
graphs, and small examples where the layout matters.

    n = Net({"A": (0, 0), "B": (2, 0), "C": (1, -1.5)},
            [("A", "B"), ("B", "C", "x"), ("C", "A")])
    self.play(n.paint("B", T.focus))
    self.play(Create(n.ring("C")))

`pos`: {key: (x, y)}. A key's label is the key itself unless `names` gives one
(use "\\n" for a two-line label). `edges`: (a, b) or (a, b, label).
`boxes=True` draws rounded boxes instead of circles (e.g. DFA states with long names).
`bend`: {(a, b): angle} curves those edges.

For graphs read from a file and laid out automatically, and for the DFS/BFS
coloring conventions, see GraphView in lectern.structures.graph.
"""

import numpy as np
from manim import Arrow, Circle, CurvedArrow, DOWN, Line, RoundedRectangle, Text, VGroup

from lectern.geometry import box_point, circle_point
from lectern.theme import T
from lectern.alt import AltText, count, describe_tree, words

__all__ = ["Net"]


class Net(AltText, VGroup):

    def __init__(self, pos, edges=(), directed=True, boxes=False, font_size=26, radius=0.3,
                 bend=None, names=None, edge_font=22, shift_labels=None):
        super().__init__()
        self.directed = directed
        self.boxes = boxes
        self.bend = bend or {}
        self.edge_font = edge_font
        self.nodes_ = {}
        self.edges_ = {}
        self.edge_labels = {}
        self.node_group = VGroup()
        self.edge_group = VGroup()
        names = names or {}
        self.names = names
        self.edge_text = {}
        for key, xy in pos.items():
            text = names.get(key, key)
            label = VGroup(*[Text(t, font_size=font_size, color=T.text) for t in str(text).split("\n")]).arrange(DOWN, buff=0.08)
            if boxes:
                shape = RoundedRectangle(width=label.width + 0.3, height=label.height + 0.25, corner_radius=0.1,
                                         color=T.text, stroke_width=2, fill_opacity=0)
            else:
                shape = Circle(radius=radius, color=T.text, stroke_width=2, fill_opacity=0)
            node = VGroup(shape, label).move_to([xy[0], xy[1], 0])
            self.nodes_[key] = node
            self.node_group.add(node)
        for e in edges:
            self.add_edge(*e)
        self.add(self.edge_group, self.node_group)

    def describe(self):
        kind = "A directed" if self.directed else "An undirected"
        name = {k: str(self.names.get(k, k)).replace("\n", " ") for k in self.nodes_}
        out = [f"{kind} graph with {count(len(name), 'node')}: {words(name.values())}."]
        if self.edges_:
            join = "to" if self.directed else "and"
            parts = [f"{name[a]} {join} {name[b]}" + (f", labeled {self.edge_text[(a, b)]}" if self.edge_text.get((a, b)) is not None else "")
                     for a, b in self.edges_]
            out.append(f"{count(len(parts), 'edge').capitalize()}: {'; '.join(parts)}.")
        return " ".join(out)

    def make_edge(self, a, b, label=None):
        """A new edge mobject from a to b (not added to the graph)."""
        na, nb = self.nodes_[a], self.nodes_[b]
        d = nb.get_center() - na.get_center()
        at = box_point if self.boxes else circle_point
        p, q = at(na, d), at(nb, -d)
        angle = self.bend.get((a, b), 0)
        if self.directed:
            if angle:
                line = CurvedArrow(p, q, angle=angle, stroke_width=2.5, tip_length=0.16, color=T.text)
            else:
                line = Arrow(p, q, buff=0, stroke_width=2.5, tip_length=0.16, color=T.text,
                             max_stroke_width_to_length_ratio=100, max_tip_length_to_length_ratio=0.4)
        else:
            line = Line(p, q, stroke_width=2.5, color=T.text)
        if label is not None:
            mid = line.point_from_proportion(0.5)
            n = np.array([-d[1], d[0], 0]) / (np.linalg.norm(d) + 1e-9)  # to the left of the edge
            tag = Text(str(label), font_size=self.edge_font, color=T.text).move_to(mid + n * 0.22)
            return VGroup(line, tag)
        return VGroup(line)

    def add_edge(self, a, b, label=None):
        e = self.make_edge(a, b, label)
        self.edges_[(a, b)] = e
        self.edge_text[(a, b)] = label
        self.edge_group.add(e)
        return e

    def node(self, k):
        return self.nodes_[k]

    def edge(self, a, b):
        return self.edges_[(a, b)]

    def paint(self, k, color, opacity=0.45):
        """Animation: fill a vertex and color its outline."""
        return self.nodes_[k][0].animate.set_fill(color, opacity=opacity).set_stroke(color, width=3)

    def ring(self, k, color=None):
        """A ring around a vertex (not added): the current vertex, by default."""
        return Circle(radius=self.nodes_[k].width / 2 + 0.07, color=color or T.current, stroke_width=4).move_to(self.nodes_[k])
