"""Binary tree visual utilities for Manim.

This module implements a binary tree visualization where each node is rendered
as a box with a value on the left and two height-tall pointer squares on the
right (left child, right child), separated by two vertical dividers -- the
same box language as `structures.linked_list.LinkedListCell`, extended to two
pointers. A null child is drawn inline as an X inside its own pointer square
(there is no shared nil sentinel like `LinkedListCell` uses, since each node
carries its own null slots).

Every node's logical `position` is tracked as plain data on the node, kept in
sync the moment a re-layout or move is requested, independent of whatever the
underlying mobject is actually rendering (which may still be mid-`.animate`
transition). Pointer arrows are always (re)drawn from this stored position
data plus each node's fixed geometry, since a node can be relocated to an
arbitrary point (not just a standard tree slot), so a target's on-screen
"forward" direction can no longer be assumed the way `LinkedListCell` assumes
it for a linear list.
"""

from typing import List, Optional
from manim import *
import numpy as np
from lectern.theme import T


def _rect_boundary_point(center, half_width, half_height, direction):
    """Point where the ray from `center` toward `direction` exits an
    axis-aligned `half_width` x `half_height` rectangle centered at `center`."""
    dx, dy = direction[0], direction[1]
    if dx == 0 and dy == 0:
        return np.array(center)
    scales = []
    if dx != 0:
        scales.append(half_width / abs(dx))
    if dy != 0:
        scales.append(half_height / abs(dy))
    scale = min(scales)
    return np.array(center) + np.array([dx, dy, 0]) * scale


class TreeNode(VGroup):
    """Visual binary-tree node: a width x height box with a value on the left
    and two height-tall pointer squares (left child, right child) at the right
    end, each holding a dot (+ arrow) when occupied or an X when null.

        |<---------------- width ---------------->|
        [      value      |  L-ptr  |  R-ptr  ]
    """

    def __init__(self, value, width=1.8, height=0.9, font_size=24):
        super().__init__()
        self.width = width
        self.height = height
        self.font_size = font_size
        self.value = value
        self.position = np.array(ORIGIN, dtype=float)

        self.parent: Optional["TreeNode"] = None
        self.parent_side: Optional[str] = None
        self.left_child: Optional["TreeNode"] = None
        self.right_child: Optional["TreeNode"] = None
        self.pinned = False

        ptr_size = 2 * height / 3
        self._divider1_x = width / 2 - 2 * ptr_size
        self._divider2_x = width / 2 - ptr_size

        self.box = Rectangle(
            width=width,
            height=height,
            stroke_color=T.text,
            stroke_width=2,
            fill_opacity=0,
        )
        self.divider1 = Line(
            np.array([self._divider1_x, height / 2, 0]),
            np.array([self._divider1_x, -height / 2, 0]),
            color=T.text,
        )
        self.divider2 = Line(
            np.array([self._divider2_x, height / 2, 0]),
            np.array([self._divider2_x, -height / 2, 0]),
            color=T.text,
        )

        label_x = -height / 2
        self.label = Text(str(value), font_size=font_size).move_to(np.array([label_x, 0, 0]))

        self.left_arrow: Optional[Arrow] = None
        self.right_arrow: Optional[Arrow] = None
        # Add the box first: `self.height`/`self.width` are Manim's computed-size
        # properties, so `_make_null` reads 0 (a flattened X) on an empty group.
        self.add(self.box, self.divider1, self.divider2, self.label)
        self.left_slot = self._make_null("left")
        self.right_slot = self._make_null("right")
        # What each slot currently *shows* ("dot" or "null"). Slots are morphed
        # in place (see `_set_slot`), so their Python type no longer says.
        self.slot_kind = {"left": "null", "right": "null"}
        self.add(self.left_slot, self.right_slot)

    def _slot_bounds(self, side):
        if side == "left":
            return self._divider1_x, self._divider2_x
        return self._divider2_x, self.width / 2

    def _slot_center_x(self, side):
        x0, x1 = self._slot_bounds(side)
        return (x0 + x1) / 2

    def slot_offset(self, side):
        return np.array([self._slot_center_x(side), 0, 0])

    def slot_dot_point(self, side):
        """Analytically-computed center of the pointer dot for `side`, based
        on the node's stored logical `position` (not its live mobject center)."""
        return self.position + self.slot_offset(side)

    def _make_dot(self, side):
        # Positioned at this node's current logical `position`, not raw local-origin
        # coordinates -- this mobject replaces one that's already at that world
        # position (see `set_value`'s analogous use of `get_center()`).
        return Dot(radius=self.height / 8, color=T.text).move_to(self.position + self.slot_offset(side))

    def _make_null(self, side):
        x0, x1 = self._slot_bounds(side)
        margin_x = (x1 - x0) * 0.2
        margin_y = self.height * 0.2
        x_left, x_right = x0 + margin_x, x1 - margin_x
        y_top, y_bottom = self.height / 2 - margin_y, -self.height / 2 + margin_y
        base = self.position
        line1 = Line(base + np.array([x_left, y_top, 0]), base + np.array([x_right, y_bottom, 0]), color=T.text)
        line2 = Line(base + np.array([x_left, y_bottom, 0]), base + np.array([x_right, y_top, 0]), color=T.text)
        return VGroup(line1, line2)

    def child_slot(self, side):
        return self.left_slot if side == "left" else self.right_slot

    def child_arrow(self, side):
        return self.left_arrow if side == "left" else self.right_arrow

    def _set_slot(self, side, new_mobject) -> Animation:
        # Morph the on-screen slot in place and keep it as the slot: it's the
        # member of this node's VGroup, so it's the one that moves/fades with
        # the node. (Swapping in `new_mobject` would leave the displayed slot
        # orphaned and the next change animating an off-screen copy.)
        self.slot_kind[side] = "dot" if isinstance(new_mobject, Dot) else "null"
        return Transform(self.child_slot(side), new_mobject)

    def set_child_null(self, side) -> List[Animation]:
        anims = [self._set_slot(side, self._make_null(side))]
        arrow = self.child_arrow(side)
        if arrow is not None:
            anims.append(FadeOut(arrow))
            if side == "left":
                self.left_arrow = None
            else:
                self.right_arrow = None
        return anims

    def set_child_dot(self, side) -> Animation:
        return self._set_slot(side, self._make_dot(side))

    def point_to(self, side, start, end, tip_length=0.15) -> Animation:
        """Build or update this side's pointer arrow. The arrow is *not* added to
        this node's own VGroup -- it's a relationship between two independently-
        moving boxes, and living inside either endpoint's group would mean a plain
        `node.animate.shift(...)` (meant only for the box/label/slot) drags the
        arrow along too, double-animating it alongside this method's own
        Create/Transform in the same `play()` call. `Tree` owns arrow mobjects
        (adds them to itself) precisely to avoid that."""
        new_arrow = Arrow(start, end, buff=0, stroke_width=2, tip_length=tip_length, color=T.text)
        current = self.child_arrow(side)
        if current is None:
            if side == "left":
                self.left_arrow = new_arrow
            else:
                self.right_arrow = new_arrow
            return Create(new_arrow)
        # Mutate the existing (already on-screen, parented) arrow in place, same
        # reasoning as LinkedListCell.point_to -- reassigning to new_arrow would
        # leave the real, displayed arrow stale.
        return Transform(current, new_arrow)

    def set_value(self, value) -> Animation:
        new_label = Text(str(value), font_size=self.font_size).move_to(self.label.get_center())
        anim = Transform(self.label, new_label)
        self.value = value
        self.label = new_label
        return anim

    def set_background(self, color, opacity=0.4) -> Animation:
        return self.box.animate.set_fill(color, opacity=opacity)

    def clear_background(self) -> Animation:
        return self.box.animate.set_fill(opacity=0)

    def highlight(self, color=None) -> Animation:
        color = T.focus if color is None else color
        return self.box.animate.set_fill(color, opacity=0.35)

    def unhighlight(self) -> Animation:
        return self.box.animate.set_fill(opacity=0)


class Tree(VGroup):
    """Container for a binary tree of TreeNodes: standard layout, with
    insertion, leaf removal, pointer rewiring, and arbitrary node relocation."""

    def __init__(
        self,
        root_value=None,
        node_width=1.8,
        node_height=0.9,
        level_gap=1.4,
        sibling_gap=0.9,
        start_point=ORIGIN,
        font_size=24,
    ):
        super().__init__()
        self.node_width = node_width
        self.node_height = node_height
        self.level_gap = level_gap
        self.sibling_gap = sibling_gap
        self.start_point = np.array(start_point, dtype=float)
        self.font_size = font_size

        self.root: Optional[TreeNode] = None
        if root_value is not None:
            self.root = TreeNode(root_value, width=node_width, height=node_height, font_size=font_size)
            self.root.position = self.start_point.copy()
            self.root.shift(self.root.position - self.root.box.get_center())
            self.add(self.root)

    def _all_nodes(self) -> List[TreeNode]:
        nodes = []
        stack = [self.root] if self.root is not None else []
        while stack:
            node = stack.pop()
            if node is None:
                continue
            nodes.append(node)
            stack.append(node.left_child)
            stack.append(node.right_child)
        return nodes

    def _assign_positions(self):
        """Standard, overlap-free binary tree layout: in-order traversal hands
        out increasing x-slots, depth sets y. Pinned nodes still consume a
        slot (so siblings don't collide with the gap they'd occupy) but their
        own position is left out of the result."""
        targets = {}
        counter = [0]

        def visit(node, depth):
            if node is None:
                return
            visit(node.left_child, depth + 1)
            slot = counter[0]
            counter[0] += 1
            if not node.pinned:
                x = self.start_point[0] + slot * self.sibling_gap
                y = self.start_point[1] - depth * self.level_gap
                targets[node] = np.array([x, y, 0.0])
            visit(node.right_child, depth + 1)

        visit(self.root, 0)
        return targets

    def _move_to_animation(self, node, target_position) -> Animation:
        delta = np.array(target_position) - node.box.get_center()
        return node.animate.shift(delta)

    def _refresh_pointer(self, node, side, force=False) -> Optional[Animation]:
        child = node.left_child if side == "left" else node.right_child
        if child is None:
            if not force and node.slot_kind[side] != "dot":
                return None
            return AnimationGroup(*node.set_child_null(side))

        anims = []
        if force or node.slot_kind[side] != "dot":
            anims.append(node.set_child_dot(side))
        start = node.slot_dot_point(side)
        direction = node.position - child.position
        if np.allclose(direction[:2], 0):
            direction = np.array([0.0, -1.0, 0.0])
        end = _rect_boundary_point(child.position, child.width / 2, child.height / 2, direction)

        is_new_arrow = node.child_arrow(side) is None
        anims.append(node.point_to(side, start, end))
        if is_new_arrow:
            self.add(node.child_arrow(side))
        return AnimationGroup(*anims)

    def layout(self) -> List[Animation]:
        targets = self._assign_positions()
        anims: List[Animation] = []
        for node, target in targets.items():
            if not np.allclose(node.position, target):
                node.position = target
                anims.append(self._move_to_animation(node, target))

        for node in self._all_nodes():
            for side in ("left", "right"):
                refreshed = self._refresh_pointer(node, side)
                if refreshed is not None:
                    anims.append(refreshed)

        return anims

    def add_node(self, value, parent: TreeNode, side: str) -> List[Animation]:
        current = parent.left_child if side == "left" else parent.right_child
        if current is not None:
            raise ValueError(f"{side} child is already occupied")

        new_node = TreeNode(value, width=self.node_width, height=self.node_height, font_size=self.font_size)
        new_node.parent = parent
        new_node.parent_side = side
        if side == "left":
            parent.left_child = new_node
        else:
            parent.right_child = new_node
        self.add(new_node)

        target = self._assign_positions()[new_node]
        new_node.position = target
        new_node.shift(new_node.position - new_node.box.get_center())

        anims = self.layout()
        return [FadeIn(new_node), *anims]

    def remove_node(self, node: TreeNode) -> List[Animation]:
        if node.left_child is not None or node.right_child is not None:
            raise ValueError("remove_node only supports removing leaf nodes")

        parent = node.parent
        if parent is None:
            self.root = None
        elif node.parent_side == "left":
            parent.left_child = None
        else:
            parent.right_child = None

        anims = self.layout()
        return [FadeOut(node), *anims]

    def set_pointer(self, parent: TreeNode, side: str, target: Optional[TreeNode] = None) -> Animation:
        if side == "left":
            parent.left_child = target
        else:
            parent.right_child = target
        if target is not None:
            target.parent = parent
            target.parent_side = side
        return self._refresh_pointer(parent, side, force=True)

    def move_node(self, node: TreeNode, position) -> List[Animation]:
        node.pinned = True
        node.position = np.array(position, dtype=float)
        anims = [self._move_to_animation(node, node.position)]
        for side in ("left", "right"):
            anims.append(self._refresh_pointer(node, side, force=True))
        if node.parent is not None:
            anims.append(self._refresh_pointer(node.parent, node.parent_side, force=True))
        return anims

    def free_node(self, node: TreeNode) -> List[Animation]:
        """Fade `node` out the way C's `free` would: its own outgoing arrows go
        with it, but its parent's pointer is left alone -- a dangling arrow to
        the empty spot until `rewire`/`set_pointer` redirects it. `node`'s
        children stay where they are, detached from it."""
        anims = [FadeOut(node)]
        for side in ("left", "right"):
            arrow = node.child_arrow(side)
            if arrow is not None:
                anims.append(FadeOut(arrow))
                self.remove(arrow)
        for child in (node.left_child, node.right_child):
            if child is not None and child.parent is node:
                child.parent = None
        self.remove(node)
        return anims

    def rewire(self, links=(), moves=None) -> List[Animation]:
        """Several pointer changes and node moves as one animation, without
        re-running the standard layout. `links` is `(parent, side, child)`
        triples (`child=None` X's the pointer box out); `moves` maps a node to
        its new position (moved nodes are pinned). Every pointer touching a
        changed link or a moved node is redrawn once."""
        touched = {}
        for parent, side, child in links:
            if side == "left":
                parent.left_child = child
            else:
                parent.right_child = child
            if child is not None:
                child.parent = parent
                child.parent_side = side
            touched[(parent, side)] = None

        anims: List[Animation] = []
        moves = moves or {}
        for node, position in moves.items():
            node.pinned = True
            node.position = np.array(position, dtype=float)
            anims.append(self._move_to_animation(node, node.position))
        for node in moves:
            touched[(node, "left")] = None
            touched[(node, "right")] = None
            if node.parent is not None:
                touched[(node.parent, node.parent_side)] = None

        for node, side in touched:
            refreshed = self._refresh_pointer(node, side)
            if refreshed is not None:
                anims.append(refreshed)
        return anims

    def unpin_node(self, node: TreeNode) -> List[Animation]:
        node.pinned = False
        return self.layout()

    @classmethod
    def from_spec(cls, spec, center=None, **kwargs) -> "Tree":
        """Build a finished tree from the `binTree[...]` bracket syntax (see
        SCRIPT_CONVENTIONS.md): first child is left, second is right, `_` is an
        explicit missing child. Built statically -- nothing to play, just
        `FadeIn` the result. With `center`, `start_point` is chosen so the
        finished tree's slots/levels are centered there."""
        from lectern.structures.tree_spec import parse_tree_spec

        parsed = parse_tree_spec(spec)

        def count(p):
            return 0 if p is None else 1 + sum(count(c) for c in p[1])

        def depth(p):
            return 0 if p is None else 1 + max([depth(c) for c in p[1]] or [0])

        if center is not None:
            sibling_gap = kwargs.get("sibling_gap", 0.9)
            level_gap = kwargs.get("level_gap", 1.4)
            kwargs["start_point"] = (np.array(center, dtype=float)
                                     + LEFT * (count(parsed) - 1) * sibling_gap / 2
                                     + UP * (depth(parsed) - 1) * level_gap / 2)

        def value(label):
            return int(label) if label.lstrip("-").isdigit() else label

        tree = cls(root_value=value(parsed[0]), **kwargs)

        def attach(parent, children):
            if len(children) > 2:
                raise ValueError(f"binTree node {parent.value!r} has more than two children")
            for side, child in zip(("left", "right"), children):
                if child is None:
                    continue
                node = TreeNode(value(child[0]), width=tree.node_width, height=tree.node_height,
                                font_size=tree.font_size)
                node.parent = parent
                node.parent_side = side
                if side == "left":
                    parent.left_child = node
                else:
                    parent.right_child = node
                tree.add(node)
                attach(node, child[1])

        attach(tree.root, parsed[1])
        tree.snap()
        return tree

    def snap(self):
        """Apply the standard layout instantly (no Animation): move every node to
        its slot and rebuild every pointer slot/arrow in place. For building a
        finished tree before it's shown; `layout()` is the animated equivalent."""
        for node, target in self._assign_positions().items():
            node.position = target
            node.shift(target - node.box.get_center())
        for node in self._all_nodes():
            for side in ("left", "right"):
                child = node.left_child if side == "left" else node.right_child
                node.remove(node.child_slot(side))
                slot = node._make_dot(side) if child is not None else node._make_null(side)
                node.add(slot)
                node.slot_kind[side] = "dot" if child is not None else "null"
                old_arrow = node.child_arrow(side)
                if old_arrow is not None:
                    self.remove(old_arrow)
                arrow = None
                if child is not None:
                    start = node.slot_dot_point(side)
                    direction = node.position - child.position
                    end = _rect_boundary_point(child.position, child.width / 2, child.height / 2, direction)
                    arrow = Arrow(start, end, buff=0, stroke_width=2, tip_length=0.15, color=T.text)
                    self.add(arrow)
                if side == "left":
                    node.left_slot, node.left_arrow = slot, arrow
                else:
                    node.right_slot, node.right_arrow = slot, arrow
        return self

    def set_root(self, value) -> Animation:
        """Give an empty tree (`Tree()` with no `root_value`) its root node."""
        if self.root is not None:
            raise ValueError("tree already has a root")
        self.root = TreeNode(value, width=self.node_width, height=self.node_height, font_size=self.font_size)
        self.root.position = self.start_point.copy()
        self.root.shift(self.root.position - self.root.box.get_center())
        self.add(self.root)
        return FadeIn(self.root)

    def highlight_node(self, node: TreeNode, color=None) -> Animation:
        color = T.focus if color is None else color
        return node.highlight(color)

    def unhighlight_node(self, node: TreeNode) -> Animation:
        return node.unhighlight()

    def set_background_node(self, node: TreeNode, color, opacity=0.4) -> Animation:
        return node.set_background(color, opacity=opacity)

    def clear_background_node(self, node: TreeNode) -> Animation:
        return node.clear_background()


__all__ = ["TreeNode", "Tree"]
