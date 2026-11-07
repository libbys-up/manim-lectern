"""The `tree[...]` / `binTree[...]` bracket syntax from SCRIPT_CONVENTIONS.md (LaTeX
qtree with the leading dots dropped). Every tree structure builds from this.

    parse_tree_spec("a [b c d] e")        # or "[a [b c d] e]", or "tree[a [b c d] e]"
    -> ("a", [("b", [("c", []), ("d", [])]), ("e", [])])

Each node is a (label, children) tuple. With placeholders=True (the default), a `_`
is an explicit missing child and parses as None, which binary trees need. With
placeholders=False, `_` is an ordinary label.
"""

import re

__all__ = ["parse_tree_spec"]


def parse_tree_spec(spec, placeholders=True):
    s = spec.strip()
    s = re.sub(r"^(tree|binTree)\s*", "", s)
    if not s.startswith("["):
        s = "[" + s + "]"
    tokens = re.findall(r"\[|\]|[^\s\[\]]+", s)
    pos = 0

    def parse_item():
        nonlocal pos
        tok = tokens[pos]
        if tok == "[":
            pos += 1
            label = tokens[pos]
            pos += 1
            children = []
            while tokens[pos] != "]":
                children.append(parse_item())
            pos += 1
            return (label, children)
        if tok == "]":
            raise ValueError(f"unexpected ']' in tree spec {spec!r}")
        pos += 1
        return None if placeholders and tok == "_" else (tok, [])

    result = parse_item()
    if pos != len(tokens):
        raise ValueError(f"trailing tokens in tree spec {spec!r}")
    return result
