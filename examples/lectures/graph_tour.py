"""Example for lectern.extras.graphs: the script is scripts/graph_tour.md."""

from manim import *
from lectern import *
from lectern.extras.graphs import *


class GraphTour(SlideScene):
    def construct(self):
        # terminology: highlight, neighborhood, walk
        g = house()
        self.panes("Terminology",
            left=["* $v_1 \\sim v_2$ if they share an edge", P,
                  "* $N(b)$ is everything next to $b$", P,
                  "* a *walk* can repeat vertices"],
            right=[g])
        self.play(g.light(["a", "b"], [("a", "b")]))
        self.pause()
        self.play(g.unlight_all())
        self.play(g.light_neighborhood("b", with_edges=True))
        self.pause()
        self.play(g.unlight_all())
        self.play(g.walk("bacbdec"))
        self.pause()

        # representations
        self.new_slide("Representations")
        h = house(weighted=True).scale(0.8)
        m = AdjacencyMatrix.from_graph(h)
        l = AdjacencyList.from_graph(h)
        row = VGroup(h, l, m).arrange(RIGHT, buff=0.8)
        self.fit_box(row, -6.5, 6.5, self.top_y(), -3.6)
        self.play(FadeIn(row))
        self.play(m.light_row("b"), l.light_row("b"), h.light_neighborhood("b", with_edges=True))
        self.pause()

        # Kruskal on the weighted house
        self.new_slide("Kruskal's Algorithm")
        k = house(weighted=True)
        el = EdgeList.from_graph(k)
        VGroup(k, el).arrange(RIGHT, buff=1.5)
        self.fit_box(VGroup(k, el), -6.5, 6.5, self.top_y(), -3.6)
        self.play(FadeIn(k))
        self.play(el.gather_from(k))
        self.play(el.sort_by_weight())
        self.pause()
        for u, v, w, ok in kruskal(k.vertices, k.weights):
            self.play(el.light(u, v), k.light(edges=[(u, v)]))
            self.play(el.mark(u, v, ok), k.color_edge(u, v, T.good if ok else T.bad))
        self.pause()

        # bipartite ripple, then the same graph as rings
        self.new_slide("Bipartite?")
        k33 = "{a : [b,d,f], b : [a,c,e], c : [b,d,f], d : [a,c,e], e : [b,d,f], f : [a,c,e]}"
        b = adj_graph(k33, layout=bipartite_layout("ace", "bdf"))
        self.anchor(b, "center")
        self.play(FadeIn(b))
        levels = bfs_levels(k33, "c")
        self.play(b.ripple(levels))
        self.pause()
        self.play(b.unlight_all())
        self.play(b.morph_to(rings_layout(levels)))
        self.play(b.ripple(levels, keep=True))
        self.pause()

        # isomorphism: Petersen star into Petersen circle
        self.new_slide("Same Graph?")
        s = petersen("star")
        c = petersen("circle")
        VGroup(s, c).arrange(RIGHT, buff=1.5)
        self.fit_box(VGroup(s, c), -6.5, 6.5, self.top_y(), -3.6)
        self.play(FadeIn(s), FadeIn(c))
        self.pause()
        self.play(FadeOut(c))
        self.play(s.animate.move_to(c), run_time=1)
        self.play(s.morph_to(PETERSEN_CIRCLE_LAYOUT, bends=PETERSEN_CIRCLE_BENDS), run_time=2.5)
        self.pause()

        # classes of graphs
        self.new_slide("Classes of Graphs")
        gs = VGroup(complete(5), empty(5), cycle(6), path(4), cube(3, dots_only=True),
                    bipartite("123", "456"))
        gs.arrange_in_grid(rows=2, buff=1.0)
        self.fit_box(gs, -6.5, 6.5, self.top_y(), -3.6)
        self.play(FadeIn(gs))
        self.pause()
