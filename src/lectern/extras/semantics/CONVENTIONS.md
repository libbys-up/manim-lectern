# Semantics conventions

Script directives for type systems and formal semantics. `Rule` is in `__init__.py`.

## Inference rules

```
[rule: e_1 : int ;; e_2 : int => e_1 + e_2 : int]
```

Premises separated by `;;`, then `=>`, then the conclusion: premises on top, a bar,
the conclusion below. An axiom has no premises: `[rule: => true : boolean]`. Every
premise and the conclusion are separate mobjects, because scripts highlight them
separately (`r.text()`, `r.heads()`, `r.con`).

In code: `Rule(["e_1 : int", "e_2 : int"], "e_1 + e_2 : int", name=r"\textsc{Add}")`.

## Derivations

A derivation is rules stacked on rules: a premise can itself be a `Rule`. Scripts
build them from the root upward, one rule at a time. Keep the earlier parts where
they are and make room by moving subtrees sideways, never by rebuilding the whole
derivation.

## Semantic brackets

`\llbracket e \rrbracket` (⟦e⟧) is available in any math once this extra is
imported (it adds the stmaryrd LaTeX package).
