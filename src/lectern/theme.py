"""Themes: every color, font, and code style a lecture uses, in one place.

Lectures and structures never name a color directly. They ask for a *role*:

    from lectern import T

    self.play(cell.animate.set_fill(T.focus, opacity=0.4))

`T` always reads the active theme, so the same lecture renders in any theme.

Roles (the meanings are part of the conventions; see conventions/STYLE.md):

    background  the frame
    text        ordinary text and strokes
    muted       dead or discarded: garbage, popped values, faded hints
    focus       what we're looking at right now
    good        matched, found, correct, reachable
    bad         error, conflict, clobbered
    current     the current position: a cursor, $sp, the current vertex
    label       small annotations: addresses, register names, offsets
    subtle      secondary text: a token's kind, a handout tag
    panel       fill behind a terminal or other inset box
    palette     extra colors for categories with no fixed meaning (T.palette[0], ...)
    code_*      code block colors (see code.py); code_background "" keeps manim's dark gray

Choosing a theme, highest priority first:

1. The LECTERN_THEME environment variable: a theme name, or a path to a .toml file.
   Use this to re-render without touching any code, e.g. for a colorblind student:
       LECTERN_THEME=dark-colorblind manim-slides render lectures/bst.py Bst
2. A scene's `theme` class attribute, e.g. `theme = "light"`.
3. `theme = "..."` in lectern.toml in the directory you render from.
4. "dark".

Defining your own theme in lectern.toml (no Python needed). Start from a built-in
theme with `base` and change only what you need:

    theme = "mine"

    [themes.mine]
    base = "dark"
    focus = "#FFB000"
    body_font = "Atkinson Hyperlegible"
"""

import dataclasses
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["Theme", "T", "BUILTIN", "get_theme", "use_theme", "current_theme", "register_theme"]


@dataclass(frozen=True)
class Theme:
    name: str
    background: str
    text: str
    muted: str
    focus: str
    good: str
    bad: str
    current: str
    label: str = "#9CDCEB"  # small annotations: addresses, register names, offsets
    subtle: str = "#BBBBBB"  # secondary text: a token's kind, a handout tag
    panel: str = "#111111"  # fill behind a terminal or other inset box
    palette: tuple = ()
    # Pygments style for code blocks. Pick one that reads well on `background`.
    code_style: str = "monokai"
    # Fill behind code blocks. "" keeps manim's own (dark gray), which suits dark styles.
    code_background: str = ""
    # Colors lectern paints on top of the Pygments style: `//:` comment lines, and
    # languages Pygments doesn't know (see code.register_painter).
    code_text: str = "#E6E6E6"
    code_comment: str = "#75715E"
    code_keyword: str = "#66D9EF"
    code_label: str = "#E6DB74"
    code_variable: str = "#FD971F"
    body_font: str = ""  # "" means manim's default font
    mono_font: str = "Monospace"

    def replace(self, **changes):
        """A copy of this theme with some fields changed."""
        return dataclasses.replace(self, **changes)


# Okabe & Ito (2008), "Color Universal Design": distinguishable under the common
# forms of color blindness. https://jfly.uni-koeln.de/color/
_OKABE_ITO = {
    "orange": "#E69F00",
    "sky_blue": "#56B4E9",
    "bluish_green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "reddish_purple": "#CC79A7",
}

# Hex values of manim's YELLOW, GREEN, RED, BLUE, GRAY, ORANGE, PURPLE, TEAL, GOLD,
# so "dark" looks exactly like the lectures did before themes existed.
_DARK = Theme(
    name="dark",
    background="#000000",
    text="#FFFFFF",
    muted="#888888",
    focus="#F7D96F",
    good="#83C167",
    bad="#FC6255",
    current="#58C4DD",
    palette=("#FF862F", "#9A72AC", "#5CD0B3", "#F0AC5F"),
    code_style="monokai",
)

_LIGHT = Theme(
    name="light",
    background="#FFFFFF",
    text="#000000",
    muted="#888888",
    # Yellow disappears on white, so the light theme focuses with blue: Okabe-Ito
    # blue, 5.2:1 on white. (manim's BLUE, #58C4DD, is only 2.0:1, too faint for text.)
    focus=_OKABE_ITO["blue"],
    good="#3A8F3A",
    bad="#CF5044",
    current="#9A72AC",
    # Brown, not blue, so a label doesn't look like it's in focus.
    label="#8B4513",
    subtle="#555555",
    panel="#F2F2F2",
    palette=("#E07020", "#5CA0B3", "#C59032", "#A05A8C"),
    code_style="default",
    code_background="#F5F5F5",
    code_text="#000000",
    code_comment="#3D7B7B",
    code_keyword="#008000",
    code_label="#0000FF",
    code_variable="#A0522D",
)

_DARK_CB = _DARK.replace(
    name="dark-colorblind",
    focus=_OKABE_ITO["yellow"],
    good=_OKABE_ITO["sky_blue"],
    bad=_OKABE_ITO["vermillion"],
    current=_OKABE_ITO["reddish_purple"],
    palette=(_OKABE_ITO["orange"], _OKABE_ITO["bluish_green"], _OKABE_ITO["blue"]),
)

_LIGHT_CB = _LIGHT.replace(
    name="light-colorblind",
    focus=_OKABE_ITO["blue"],
    good=_OKABE_ITO["bluish_green"],
    bad=_OKABE_ITO["vermillion"],
    current=_OKABE_ITO["reddish_purple"],
    palette=(_OKABE_ITO["orange"], _OKABE_ITO["sky_blue"], "#7A6A00"),
)

BUILTIN = {t.name: t for t in (_DARK, _LIGHT, _DARK_CB, _LIGHT_CB)}

_registry = dict(BUILTIN)
_active = None  # set by use_theme(); None means "not chosen yet"
_project_config = None  # lectern.toml, read once


def register_theme(theme):
    """Make `theme` available by name (to use_theme, LECTERN_THEME, and lectern.toml)."""
    _registry[theme.name] = theme
    return theme


def _load_project_config():
    """Read lectern.toml from the working directory, once. Registers any [themes.*] it defines."""
    global _project_config
    if _project_config is None:
        path = Path("lectern.toml")
        _project_config = tomllib.loads(path.read_text()) if path.exists() else {}
        _register_toml_themes(_project_config)
    return _project_config


def _register_toml_themes(config):
    for name, fields in config.get("themes", {}).items():
        fields = dict(fields)
        base = get_theme(fields.pop("base", "dark"))
        if "palette" in fields:
            fields["palette"] = tuple(fields["palette"])
        register_theme(base.replace(name=name, **fields))


def get_theme(name_or_path):
    """A theme by name, or from a .toml file that defines exactly one [themes.*] table."""
    if str(name_or_path).endswith(".toml"):
        config = tomllib.loads(Path(name_or_path).read_text())
        _register_toml_themes(config)
        names = list(config.get("themes", {}))
        if len(names) != 1:
            raise ValueError(f"{name_or_path} should define exactly one [themes.<name>] table")
        return _registry[names[0]]
    _load_project_config()
    try:
        return _registry[name_or_path]
    except KeyError:
        known = ", ".join(sorted(_registry))
        raise ValueError(f"unknown theme {name_or_path!r}; known themes: {known}") from None


def use_theme(requested=None):
    """Pick the active theme (see the module docstring for the order) and return it.

    `requested` is the scene's own choice, which LECTERN_THEME still overrides."""
    global _active
    choice = (
        os.environ.get("LECTERN_THEME")
        or requested
        or _load_project_config().get("theme")
        or "dark"
    )
    _active = choice if isinstance(choice, Theme) else get_theme(choice)
    return _active


def current_theme():
    """The active theme, choosing one if nothing has yet."""
    return _active if _active is not None else use_theme()


_NOT_COLORS = {"name", "code_style", "code_background", "body_font", "mono_font"}


class _ThemeRoles:
    """`T`: the active theme's roles, read at the moment you use them.

    Colors come back as manim ManimColor objects (the theme stores hex strings), so
    they compare equal to manim's own constants: a ManimColor compared with a plain
    string raises TypeError instead of returning False."""

    def __getattr__(self, role):
        value = getattr(current_theme(), role)
        if role in _NOT_COLORS:
            return value
        from manim import ManimColor  # here, so theme.py itself doesn't need manim
        if role == "palette":
            return tuple(ManimColor(c) for c in value)
        return ManimColor(value)

    def __repr__(self):
        return f"T -> {current_theme()!r}"


T = _ThemeRoles()
