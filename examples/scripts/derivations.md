==== A grammar
add the grammar
1. E \rightarrow E + T
2. E \rightarrow T
3. T \rightarrow id
\pause
* Each line is a *production*: the left side can be replaced by the right
* `id` is a *terminal*; `E` and `T` are *nonterminals*

==== Deriving id + id
grammar at the top, derivation below it
expand E one step at a time, boxing the production used:
E, E + T, T + T, id + T, id + id
note: We always expanded the leftmost nonterminal. That's a leftmost derivation.

==== The parse tree
tree[E [E [T id]] + [T id]]
\pause
[[ highlight the + node \pause ]]
* The tree records *which* production made each node, not the order we used them
