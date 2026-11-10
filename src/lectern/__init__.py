"""manim-lectern: animated lecture slides from plain-text scripts.

    from manim import *
    from lectern import *

gives you SlideScene, the page() markers (P, N, C, H), the theme roles (T), and the
core structures. Extras are imported on their own, e.g.
`from lectern.extras.parsing import ParsingMixin`.

Start with README.md and conventions/SCRIPT_CONVENTIONS.md.
"""

from lectern.alt import AltText
from lectern.anim import Arrive, arrive
from lectern.markers import C, H, N, P
from lectern.slide import SlideScene
from lectern.code import CodeHighlighter
from lectern.structures import *  # noqa: F401,F403
from lectern.structures import __all__ as _structures
from lectern.text import mono
from lectern.theme import T, Theme, current_theme, get_theme, register_theme, use_theme

__version__ = "0.1.0.dev0"

__all__ = [
    "SlideScene", "P", "N", "C", "H", "T", "Theme", "current_theme", "get_theme", "register_theme", "use_theme",
    "Arrive", "arrive", "mono", "CodeHighlighter", "AltText",
] + _structures
