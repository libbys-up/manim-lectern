"""Alt text: what a structure shows, in words, for someone who can't see the slide.

    a = Array([3, 7, 2, 9, 4])
    a.alt_text            # "An array of 5 values: 3, 7, 2, 9, 4."

    g = GraphView.from_file("house.gr")
    g.alt_text = "The house graph: a square with a triangle on top, like a drawing of a house."
    C(Net(pos, edges).with_alt("The DFA for binary numbers divisible by 3."))

Every structure has an `alt_text`. Until you set it, it's written from the structure
as it is right now, so it keeps up with the animation: an array describes its new
order after a swap. Once you set it, it stays until you set it again. Set it back to
None to return to the automatic text.

The automatic text lists what's there. That's right for short, linear things like
arrays and lists. For a graph or a big tree, a sentence about what the picture is
*for* ("the graph from the reading, with the shortest path from A to F marked") is
usually more useful than a list of every edge, so write one.

Handouts use `alt_text` as the description of each structure's picture.

Writing a structure: inherit from AltText (before VGroup) and override `describe()`.
"""

__all__ = ["AltText", "words", "count", "describe_tree"]


class AltText:
    """Mixin for anything drawn on a slide: an `alt_text` that's automatic until set."""

    _alt = None

    @property
    def alt_text(self):
        """What this shows, in words: your text if you set one, else `describe()`."""
        return self._alt if self._alt is not None else self.describe()

    @alt_text.setter
    def alt_text(self, text):
        self._alt = text

    def with_alt(self, text):
        """Set `alt_text` and return self, so it fits inside a page() list:
        `C(Array([3, 7, 2]).with_alt("The input."))`."""
        self.alt_text = text
        return self

    def describe(self):
        """The automatic alt text. Structures override this."""
        return "A diagram."


def words(items, conj="and"):
    """Items as a phrase: ["a"] -> "a"; ["a", "b"] -> "a and b"; three or more are
    joined with commas and a final `conj`."""
    items = [str(i) for i in items]
    if len(items) <= 1:
        return "".join(items)
    if len(items) == 2:
        return f"{items[0]} {conj} {items[1]}"
    return ", ".join(items[:-1]) + f", {conj} {items[-1]}"


def count(n, noun, plural=None):
    """`count(1, "vertex", "vertices")` -> "1 vertex"; `count(3, "edge")` -> "3 edges"."""
    return f"{n} {noun if n == 1 else (plural or noun + 's')}"


def describe_tree(root, children, label, sides=None):
    """Sentences describing a tree, one per internal node, in preorder:
    "The root is 8. 8 has children 3 and 10. 3 has children 1 and 6."

    `children(node)` gives a node's children (None for a missing child), and
    `label(node)` its text. For a binary tree, pass `sides=("left", "right")` to
    name each child by side: "8 has left child 3 and right child 10."
    """
    if root is None:
        return "An empty tree."
    out = [f"The root is {label(root)}."]
    stack = [root]
    while stack:
        node = stack.pop()
        kids = list(children(node))
        present = [k for k in kids if k is not None]
        if present:
            if sides:
                parts = [f"{side} child {label(k)}" for side, k in zip(sides, kids) if k is not None]
                out.append(f"{label(node)} has {words(parts)}.")
            else:
                noun = "child" if len(present) == 1 else "children"
                out.append(f"{label(node)} has {noun} {words([label(k) for k in present])}.")
        stack.extend(reversed(present))
    return " ".join(out)
