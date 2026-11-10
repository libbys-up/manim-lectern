# Script conventions

A lecture starts as a **script**: a plain-text file (`scripts/<lecture>.md`) written
in the markup below. Someone (you, or an AI agent) translates it by hand into a
lecture file (`lectures/<lecture>.py`), a `SlideScene` whose methods are named after
these directives. You render it, watch it, and write down fixes for the next pass.

There is no parser. This document is a shared vocabulary between the author and the
translator, not a grammar a program reads. Anything the markup doesn't cover is
written as plain prose (a *stage direction*), and the translator works out the code.

Two other files go with this one:

- `STYLE.md`: what a good slide looks like (colors, motion, highlighting). The
  markup says *what* is on a slide; the style says *how* it should behave.
- Your course's own conventions file, if it has one (`lectern init` creates one: `COURSE_CONVENTIONS.md`). It can
  add directives, change these, or add style rules. Where it disagrees with this
  file, the course file wins.

Extras add their own directives in `src/lectern/extras/<topic>/CONVENTIONS.md`.

## New slide

A line of **4 or more `=`**, optionally followed by a title:

```
==== Searching an Array
```

Fades out everything on screen, advances, and brings in the title: large, centered,
at the top. A bare `====` is an untitled continuation slide (`self.clear_body()`). To carry a
diagram over to the next slide, keep it while everything else fades:
`self.continue_slide("Next title", keep=[diagram])`.

In code: `self.page("Searching an Array", ...)`, or `self.new_slide("...")` for a
slide built by hand.

## Pause

A line containing only `\pause`:

```
\pause
```

Advances **without** fading: everything visible stays, and what comes next animates
in after the click. In a `page()` list it's `P`; elsewhere, `self.pause()`.

## Lists

```
* first point
* second point
  * a sub-point, indented two spaces under it
1. a numbered point
```

- `* ` starts a bullet; `1. `, `2. ` … start numbered items.
- Two more spaces of indentation nest an item under the one above. Markers step by
  depth: bullets `•` → `◦` → `▪`, numbers `1.` → `a.` → `i.`.
- Consecutive list lines are one block, revealed together. Put `\pause` between items
  to reveal them one at a time.
- In code, each item is a string in a `page()` list, written exactly as above, or use
  `self.bullets(items, ordered=...)` for a list as one group.

### Animations inside a list

Text in double square brackets inside a list is an animation to create, not text to
show:

```
<< left
tree[a [b c d] [e f g]]
<< right
* a is the *root*
  [[ highlight node a \pause ]]
* b is a *child* of a, and a is a *parent* of b
  [[ highlight a, b, and the link between them \pause ]]
* The *height* of the tree is the length of the longest path.
  [[ unhighlight everything, draw a bracket on the right of the tree
     that is tall enough for the entire tree, write 3 to the right of it \pause ]]
* This is a *binary tree* because each node has two branches
```

- The contents of `[[ ... ]]` are a stage direction (see **Plain prose** below).
  Nothing inside is shown as list text.
- An action belongs to the item it follows, on the same line or the lines under it,
  and ends at `]]`.
- An action splits the list's reveal: the items up to it appear, the animation plays,
  then the rest come in. A list with an action on every item is revealed one item at
  a time without any `\pause`.
- A `\pause` inside the brackets pauses at that point in the action. Without one, the
  next item comes in right after the animation.
- The whole list is still laid out up front, so earlier items don't move as later
  ones appear. In code, an action is a callable in the `page()` list:
  `lambda: self.play(t.lit("a"))`.
- "It", "the tree", "the array" refer to whatever is on screen. Name the structure if
  there's more than one.

## Inline emphasis

Anywhere text appears (titles, list items, table cells, boxes):

```
**bold**, *emphasis*, `code`, $x^2$, K_{5}, 2^{n}
```

- `*emphasis*` is italic in the theme's focus color.
- Nothing inside `` `code` `` is markup. Write ``` `` `+ `` ``` for code containing a
  backtick.
- `$...$` is LaTeX math, set on the same baseline as the prose around it.
- `_{...}` and `^{...}` outside math are a subscript and superscript in the prose
  font, for names like K_{5} or v_{1} that aren't really math.
- `\*` is a literal asterisk. A `*` mid-line never starts a bullet; only `* ` at the
  start of a line does.

## Text

A line starting with `text: `:

```
text: Binary search halves the range each step.
text: p_1 = (x_1, y_1)
```

The translator decides, line by line:

- **Prose** (most lines): a paragraph with inline emphasis, wrapped to fit. In a
  `page()` list it's just the string.
- **Math** (an equation, subscripts, symbols like `\le`): `self.math_text(...)`, real
  LaTeX. Inline emphasis doesn't apply inside math.

Each `text:` line is its own block. Blocks stack top to bottom (see **Positioning**).

## Tables

Markdown table syntax:

```
| n     | time    |
|-------|---------|
| 10    | 0.01ms  |
| 100   | 0.09ms  |
```

The header row is bold, with a rule under it. The whole table fades in at once unless
a stage direction says otherwise ("reveal row by row"). In code:
`t = self.table(rows)`; for row by row, `H(t), self.rows(t)` in a `page()` list.
For a table with every cell boxed (a grid), use `self.grid_table(rows)` and
`self.reveal_grid_table(t)`.

## Code blocks

A line naming a language, then the source up to the next directive or blank line:

```
java code
for (int i = 0; i < n; i++)
{
    sum += a[i];
}
```

In code: `c = self.code(SRC, lang="java")`. Highlight with `self.hl(c, 2)` (line 2)
or `self.hl(c, "sum +=")` (the line containing that text), `self.hls(c, "i++")` for
part of a line, and `self.morph(c, NEW_SRC)` to rewrite the code with only the
changed lines changing. Code kept in a file: `self.code_block(path)` with a
`CodeHighlighter`. See `lectern/code.py` for markers you can put in the source
(`//:` comment lines, `⟦placeholders⟧`).

## Definition box

```
definition box: Invariant
An *invariant* is something that is true
for every iteration of your loop.
```

A bordered callout, with the title set into its top border. If the script gives no
title, use the term the body defines (usually the one in `*emphasis*`). In code:
`self.definition_box("Invariant", [line, line])`.

## Speaker notes

A line starting with `note: ` is said, not shown:

```
note: This is the same idea as the phone book example from last time.
```

It goes in the slide's speaker notes (`N("...")` in a `page()` list, or
`self.note(...)`), which `manim-slides present` shows when you press S. Use notes for
narration, lead-ins, and asides, so the slide carries only what the viewer needs to see.

## Data structures

A bracketed directive inserts a structure from `lectern.structures`:

```
[array: 3, 1, 4, 1, 5]
[stack: push 3, push 5, pop]
[linked_list: 3, 1, 4]
```

A list of values creates the structure holding them. A list of operations plays them,
starting from empty. Anything after that (highlighting an index, drawing a pointer,
swapping) is a stage direction, or a `[[ ... ]]` action in a list. Use the
structure's own methods; don't hand-draw shapes a structure already provides.

### Alt text

A line starting with `alt: ` right after a structure gives its alt text: what the
picture says to someone who can't see it, used in handouts.

```
[graph: house.gr]
alt: The house graph: a square with a triangle on top, like a child's drawing of a house.
```

It applies from that point on, so a later `alt:` line changes it, for example after a
search has colored the graph. In code: `.with_alt("...")` on the structure, or
`g.alt_text = "..."` later.

Without an `alt:` line, the structure describes itself by listing its contents
("An array of 5 values: 3, 7, 2, 9, 4."). That's fine for arrays, lists, stacks, and
rows. For graphs, larger trees, and anything whose point isn't its contents, the
translator writes one from what the script says around it.

### Trees

`tree[...]` and `binTree[...]` share one bracket syntax (LaTeX `qtree` without the
leading dots) and differ in how the tree is drawn:

```
tree[a [b c d] e]
binTree[1 [2 3 4] [5 6 7]]
```

**Bracket syntax.** Inside brackets, the *first* item is the node's label and the
rest are its children, left to right.

- A bare label (`c`) is a leaf.
- `[label child child ...]` is a node with children. A child is a bare label or
  another bracketed subtree, to any depth.
- The brackets after `tree`/`binTree` are the root's own: `tree[a b c]` is root `a`
  with leaves `b` and `c`.
- Labels are any run of non-space, non-bracket characters (`7`, `cs305`, `+`).
- `tree [a b c]`, with a space, is fine.

```
tree[a [b c d] e]           tree[a [b [c d] e]]

        a                           a
       / \                          |
      b   e                         b
     / \                           / \
    c   d                         c   e
                                  |
                                  d
```

In the second, `[c d]` is node `c` with one child `d`, *not* two siblings. To give
`b` the two leaves `c` and `d`, write `[b c d]`.

**`tree[...]`, a plain tree**: labels and lines only, any number of children per node
(ternary trees, tries, expression trees, directory trees). Each parent is centered
over its children. In code: `PlainTree` (boxed labels) or `LabelTree` (bare labels,
for parse trees). Every node and edge is addressable, by label or by path.

**`binTree[...]`, a boxed binary tree**: the pointer-diagram form, in the same box
language as linked lists. Each node is a value box plus left and right pointer boxes,
with an arrow from each pointer to its child.

- At most two children: the first is **left**, the second **right**. More than two
  is a script error; the translator should flag it, not guess.
- A missing child's pointer box gets an X. `[label child]` has only a left child.
- `_` is an explicit missing child when the other side is present: `[5 _ 7]` has only
  a right child. (`_` is a placeholder only in `binTree`.)

In code: `Tree`, built with `Tree.from_spec(...)` or node by node with
`tree.add_node(value, parent=node, side="left"|"right")`.

## Positioning

**Left-justified by default.** The title is centered; everything below it starts at
the left margin, like a default Beamer slide. Center a block only when the script
says so (`-- center --`) or a structure clearly reads better centered.

**Default flow.** Blocks stack top to bottom, as if `<< down` were between every two.
`page()` does this, scaling everything to fit. The directives below *override* the
flow; most blocks don't need one. Neither causes a pause or a fade.

**Absolute anchor**: put the *next* block in a region of the content area:

```
-- left --
[array: 5, 3, 8, 1]
```

Regions: `left`, `right`, `up`, `down`, `center`, and corners (`up left`,
`down right`, …). In code: two columns are `self.panes(title, left=[...], right=[...])`;
otherwise `self.anchor(mob, "up left")`.

**Relative to the previous block**:

```
[code: bubble_sort.c]
<< right
[array: 5, 3, 8, 1]
```

Direction: `left`, `right`, `up`, `down`. In code: `self.right_of(..., ref=prev)`, or
`self.next_to_prev(mob, prev, "right")`.

**Structures that grow after they appear** (a `Tree` fed `add_node`, an `Array` fed
`append_value`): anchoring one when it's still small centers the small version.
Instead get the point first, `self.anchor_point("center")`, and pass it as
`start_point=` when you build the structure. `Tree.start_point` is its leftmost
in-order slot, so shift it left by `(n - 1) * sibling_gap / 2` for `n` nodes to
center the finished tree.

## Algebraic transformations

When a stage direction walks through rearranging an equation ("solve `(x+1)*3 = 4`
for `x`"), don't make one `MathTex` per step and `Transform` the whole thing. LaTeX
rebuilds the whole string every step, so parts that didn't change (`x+1`) visibly
rebuild too, which undercuts the point.

Split the equation into pieces up front, move only the pieces that move, and
`Transform` only the piece whose *content* changes:

```python
lhs = self.math_text("x+1")  # never touched again
times, three = self.math_text(r"\cdot"), self.math_text("3")
equals, four = self.math_text("="), self.math_text("4")
group = VGroup(lhs, times, three, equals, four).arrange(RIGHT)
self.play(FadeIn(group))
self.pause()

# move the 3 under the 4; lhs is untouched
self.play(FadeOut(times), three.animate.next_to(four, DOWN, buff=0.1))
self.pause()

# only now does any content change
fraction = self.math_text(r"\frac{4}{3}").move_to(VGroup(four, three))
self.play(ReplacementTransform(VGroup(four, three), fraction))
```

The same rule applies to code: `self.morph(c, NEW_SRC)` moves unchanged lines and
fades only the changed ones.

## Plain prose (stage directions)

Any line that isn't one of the above is an instruction for the translator:

```
highlight index 2
draw an arrow from the pointer variable to cell 3
swap the highlighted cells
```

This is how everything the markup doesn't cover gets expressed.

## Example

```
==== Linear Search
* Walk through the array and check each value
* Stop as soon as we find a match
\pause
[array: 3, 7, 2, 9, 4]
-- center --
\pause
highlight index 0
note: Seven isn't three, so we move on.
\pause
compare index 0 to the target and reject it
\pause
highlight index 1
```

One slide: a title and two bullets; on the first click, the array fades in, centered;
then the search goes index by index, one click per step.

See `examples/` for scripts next to the lectures translated from them.
