==== Linear Search
* Walk through the array and check each value
* Stop as soon as we find a match
note: This is the search you'd do by hand on an unsorted list.
\pause
text: Looking for **9**
[array: 3, 7, 2, 9, 4]
-- center --
\pause
highlight index 0, compare it to 9, and reject it
\pause
highlight index 1, compare, and reject it
\pause
highlight index 2, compare, and reject it
\pause
highlight index 3: it matches
note: Three comparisons failed before this one succeeded.

==== How long does it take?
* Best case: the first value matches, so $\mathcal{O}\left(1\right)$
* Worst case: no value matches, so we check all $n$, $\mathcal{O}\left(n\right)$
\pause
definition box: Linear time
An algorithm takes *linear time* when its work grows in proportion to $n$.

==== Recap
* Linear search checks each value in order
* It takes $\mathcal{O}\left(n\right)$ time in the worst case
