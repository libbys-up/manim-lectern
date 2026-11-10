The graphs extra (lectern.extras.graphs). The house graph is
AdjGraph{a : [b,c], b : [a,c,d], c : [a,b,e], d : [b,e], e : [c,d]},
drawn as a triangle on a square.

==== Terminology
put the text on the left, and the house graph on the right
 * $v_1 \sim v_2$ if they share an edge
   [[ highlight a, b, and the edge between them \pause ]]
 * $N(b)$ is everything next to $b$
   [[ highlight the neighborhood of b and its edges \pause ]]
 * a *walk* can repeat vertices
   [[ animate walking b, a, c, b, d, e, c ]]

==== Representations
the weighted house graph, its adjacency list, and its adjacency matrix, side by side
\pause
highlight the neighborhood of b in all three

==== Kruskal's Algorithm
the weighted house graph, then move each edge into a list beside it
sort the list by weight
\pause
for each edge, highlight it in the list and the graph, then mark it kept or rejected
\pause

==== Bipartite?
Draw AdjGraph{a : [b,d,f], b : [a,c,e], c : [b,d,f], d : [a,c,e], e : [b,d,f], f : [a,c,e]}
with a, c, e on top and b, d, f on the bottom.
ripple a highlight out from c
\pause
redraw it as rings around c, and ripple again, keeping each level lit
\pause

==== Same Graph?
petersenStar next to petersenCircle
\pause
animate petersenStar turning into petersenCircle
\pause

==== Classes of Graphs
K_5, E_5, C_6, P_4, Q_3, and K_{3,3} in a grid
