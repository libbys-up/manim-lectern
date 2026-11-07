# Parsing conventions

Script directives for lexing and parsing lectures. Scene methods are in
`ParsingMixin` (`__init__.py`); `chars`, `tokens`, and `LabelTree` are core structures.

## Grammars

```
add the grammar
1. E \rightarrow E + T
2. E \rightarrow T
```

Each production is its own mobject, addressable by number, in math font.
Scripts highlight productions by number. In code:
`g = self.grammar(r"E \rightarrow E + T", r"E \rightarrow T", numbered=True)`;
production 1 is `g[0]`.

## Derivations

Scripts describe a derivation as its sentential forms, one per step
("expand E: E, E + T, T + T, id + T, id + id"). Tokens that survive a step move to their new places;
only the replaced part changes. The production used at each step is boxed in the
grammar. In code: `self.expand([(None, "E"), (0, "E + T"), ...], g)`, or
`self.deriv` and `self.rewrite` for one step at a time.

## Tokens

```
[tokens: if ( ID:x > NUM:0 ) ]
```

A row of boxes, one token per box. `ID:x` is drawn with the kind on top and the
value, larger, below it. A cursor arrow (`current` color) above the row marks the
next token. In code: `r = tokens("if ( ID:x > NUM:0 )")`, `a = r.cursor(0)`,
`r.cursor_to(a, 3)`.

## Character streams (lexing)

```
[chars: abcde]
```

A row of single-character cells with no indices. Scripts draw brackets under runs of
cells to show the token being formed (`self.grow_bracket(row, i, j)`), and peek at a
character without consuming it (`self.peek_at(row, i, ok)`).

## Trees

`tree[...]` from SCRIPT_CONVENTIONS.md, drawn with `LabelTree`. Labels like `(`,
`)`, `+`, `*`, `==`, `<` are all legal. A node with a type has it written in smaller
`good`-colored text right below its label (`t.tag(node, "boolean")`).

Parse trees use the math font for nonterminals. Abstract syntax trees use the code
font and node class names (`Plus`, `IDExp`).
