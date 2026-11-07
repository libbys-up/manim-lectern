"""Layout constants shared by the slide helpers, in manim units (the frame is 14.2 x 8)."""

MARGIN = 0.6  # left and right page margins
TOP_BUFF = 0.35  # gap between a slide's title and its first block
BOTTOM = -3.75  # lowest y that page() and panes() will place content at

STEP = 0.5  # default run time of a reveal, in seconds
MIN_RUN_TIME = 0.2  # see SlideScene.play

TITLE_FONT_SIZE = 44
BODY_FONT_SIZE = 34  # page()
PANE_FONT_SIZE = 30  # panes(), txt(), styled()

MIN_SCALE = 0.45  # layout() never shrinks a block more than this...
WARN_SCALE = 0.7  # ...and reports it (see bounds.py) when it shrinks more than this
