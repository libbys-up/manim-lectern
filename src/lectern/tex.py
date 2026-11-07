"""LaTeX packages for MathTex and Tex.

    from lectern.tex import use_packages
    use_packages("stmaryrd")    # \\llbracket and \\rrbracket

Call it at import time, before anything is typeset. It changes manim's global TeX
template, so it affects every scene rendered in this process.
"""

from manim import TexTemplate, config

__all__ = ["use_packages"]

_packages = []


def use_packages(*names):
    """Add `\\usepackage{name}` for each name not already added."""
    new = [n for n in names if n not in _packages]
    if not new:
        return
    _packages.extend(new)
    template = TexTemplate()
    for n in _packages:
        template.add_to_preamble(rf"\usepackage{{{n}}}")
    config.tex_template = template
