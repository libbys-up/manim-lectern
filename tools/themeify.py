"""Convert manim color names in Python files to lectern theme roles.

    python tools/themeify.py FILE...           # rewrite the files in place
    python tools/themeify.py --dry-run FILE... # print what would change

What it does:
- `YELLOW` (as code, not in a comment or string) becomes `T.focus`, and so on
  (see ROLES). With the dark theme, every role has exactly the color it replaces,
  so a converted lecture renders the same as before.
- A default argument like `color=WHITE` can't read the theme (defaults are evaluated
  once, when the function is defined), so it becomes `color=None`, and a line at the
  top of the function fills it in: `color = T.text if color is None else color`.
- Adds `from lectern.theme import T` if the file doesn't already import T.
- Leaves other colors (ORANGE, PURPLE, hex strings, ...) alone and lists them, since
  they have no fixed meaning. Use T.palette[i] for those if they should change with
  the theme.

For code written for a white background, pass --light: BLACK becomes T.text and
WHITE becomes T.background.

Check the result: a color can mean something other than its usual role (WHITE as
the literal name of a DFS vertex state, say). Pass --keep NAME to leave a name alone.
"""

import argparse
import ast
import io
import re
import sys
import tokenize
from collections import Counter
from pathlib import Path

ROLES = {
    "WHITE": "text",
    "BLACK": "background",
    "YELLOW": "focus",
    "GREEN": "good",
    "RED": "bad",
    "BLUE": "current",
    "GRAY": "muted",
    "GREY": "muted",
    "GRAY_C": "muted",
    "GREY_C": "muted",
    "GRAY_B": "subtle",
    "GREY_B": "subtle",
    "BLUE_B": "label",
    # The course's older role names.
    "FOCUS": "focus",
    "GOOD": "good",
    "BAD": "bad",
    "CUR": "current",
    "DEAD": "muted",
}

OTHER_COLORS = re.compile(r"^(?:[A-Z]+_[A-E]|ORANGE|PURPLE|TEAL|GOLD|PINK|MAROON|LIGHT_\w+|DARK_\w+|PURE_\w+)$")


def convert(src, keep=(), light=False):
    roles = {k: v for k, v in ROLES.items() if k not in keep}
    if light:  # code written for a white background: black was the text color
        roles.update({k: v for k, v in {"BLACK": "text", "WHITE": "background"}.items() if k not in keep})
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)

    # 1. Defaults: find `arg=COLOR` in function signatures, and where to put the fix-up.
    inserts = {}  # line index -> text to insert before it
    default_spans = set()  # (line, col) of default-value names to rewrite as None
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = node.args.args + node.args.kwonlyargs
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults + node.args.kw_defaults
        fixes = []
        for a, d in zip(args, defaults):
            if isinstance(d, ast.Name) and d.id in roles:
                default_spans.add((d.lineno, d.col_offset))
                fixes.append(f"{a.arg} = T.{roles[d.id]} if {a.arg} is None else {a.arg}")
        if not fixes:
            continue
        body = node.body
        first = body[0]
        has_doc = isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) and isinstance(first.value.value, str)
        anchor = body[1] if has_doc and len(body) > 1 else (None if has_doc else first)
        if anchor is None:  # a function that is only a docstring
            at = first.end_lineno  # insert after it
            indent = re.match(r"\s*", lines[first.lineno - 1]).group(0)
        else:
            at = anchor.lineno - 1
            indent = re.match(r"\s*", lines[at]).group(0)
        inserts[at] = inserts.get(at, "") + "".join(f"{indent}{f}\n" for f in fixes)

    # 2. Every other NAME token that is a role color, outside of comments, strings,
    #    and import statements.
    import_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_lines.update(range(node.lineno, node.end_lineno + 1))
    # A name being assigned (GOOD = GREEN) is the lecture's own constant: leave it.
    stores = {(n.lineno, n.col_offset) for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    edits = []  # (line, col, old, new)
    unknown = Counter()
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type != tokenize.NAME:
            continue
        line, col = tok.start
        if line in import_lines or (line, col) in stores:
            continue
        if tok.string in roles:
            prev = lines[line - 1][:col]
            if prev.endswith(".") and not prev.endswith("T."):  # an attribute like self.WHITE: leave it
                continue
            new = "None" if (line, col) in default_spans else f"T.{roles[tok.string]}"
            edits.append((line, col, tok.string, new))
        elif OTHER_COLORS.match(tok.string) and tok.string not in keep:
            unknown[tok.string] += 1

    for line, col, old, new in sorted(edits, reverse=True):
        s = lines[line - 1]
        lines[line - 1] = s[:col] + new + s[col + len(old):]
    for at in sorted(inserts, reverse=True):
        lines.insert(at, inserts[at])

    out = "".join(lines)
    if edits and not re.search(r"^from lectern(\.theme)? import .*\bT\b|^from (lectern|scenes\.\w+) import \*", out, re.M):
        # After the last top-level import.
        imports = [n for n in ast.parse(out).body if isinstance(n, (ast.Import, ast.ImportFrom))]
        at = imports[-1].end_lineno if imports else 0
        out_lines = out.splitlines(keepends=True)
        out_lines.insert(at, "from lectern.theme import T\n")
        out = "".join(out_lines)
    return out, len(edits), unknown


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep", action="append", default=[], help="a color name to leave alone (repeatable)")
    ap.add_argument("--light", action="store_true", help="the code was written for a light background (BLACK is text)")
    args = ap.parse_args()
    total = 0
    for f in args.files:
        p = Path(f)
        src = p.read_text()
        out, n, unknown = convert(src, keep=set(args.keep), light=args.light)
        total += n
        extra = f"  other colors: {dict(unknown)}" if unknown else ""
        print(f"{f}: {n} changed{extra}")
        if not args.dry_run and out != src:
            ast.parse(out)  # never write a file that doesn't parse
            p.write_text(out)
    print(f"total: {total}")


if __name__ == "__main__":
    main()
