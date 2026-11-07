"""Data structures to draw and animate. Each module's docstring shows how to use it.

    array               Array, ArrayCell
    linked_list         LinkedList, LinkedListCell, NilCell
    doubly_linked_list  DoublyLinkedList, DoublyLinkedListCell
    stack               Stack
    tree                Tree, TreeNode (binary trees with pointer slots)
    plain_tree          PlainTree, PlainTreeNode (boxed labels, any number of children)
    label_tree          LabelTree (bare labels: parse trees, syntax trees)
    tree_spec           parse_tree_spec (the tree[...] syntax every tree builds from)
    graph               GraphView, read_gr_file (graphs from .gr files, search coloring)
    net                 Net (a graph you place by hand: state machines, CFGs)
    row                 Row, chars, tokens (a row of cells sized to their contents)
    hash_table          ChainedHashTable
    uml                 UMLClass, UMLLink
"""

from lectern.structures.array import Array, ArrayCell
from lectern.structures.doubly_linked_list import DoublyLinkedList, DoublyLinkedListCell
from lectern.structures.graph import STATE_STYLE, GraphEdge, GraphVertex, GraphView, read_gr_file
from lectern.structures.hash_table import ChainedHashTable, ChainNode
from lectern.structures.label_tree import LabelTree
from lectern.structures.linked_list import LinkedList, LinkedListCell, NilCell
from lectern.structures.net import Net
from lectern.structures.plain_tree import PlainTree, PlainTreeNode
from lectern.structures.row import Row, chars, tokens
from lectern.structures.stack import Stack
from lectern.structures.tree import Tree, TreeNode
from lectern.structures.tree_spec import parse_tree_spec
from lectern.structures.uml import UMLClass, UMLLink

__all__ = [
    "Array", "ArrayCell", "LinkedList", "LinkedListCell", "NilCell", "DoublyLinkedList", "DoublyLinkedListCell",
    "Stack", "Tree", "TreeNode", "PlainTree", "PlainTreeNode", "LabelTree", "parse_tree_spec", "GraphView",
    "GraphVertex", "GraphEdge", "STATE_STYLE", "read_gr_file", "Net", "Row", "chars", "tokens", "ChainedHashTable",
    "ChainNode", "UMLClass", "UMLLink",
]
