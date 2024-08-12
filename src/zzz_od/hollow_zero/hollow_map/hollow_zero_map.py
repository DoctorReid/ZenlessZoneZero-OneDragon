from typing import List, Optional

from one_dragon.base.geometry.rectangle import Rect
from zzz_od.operation.hollow_zero.hollow_zero_event import HollowZeroEntry


class HollowZeroMapNode:

    def __init__(self, pos: Rect, node_name: str):
        self.pos: Rect = pos
        self.node_name: str = node_name
        self.entry: Optional[HollowZeroEntry] = None


class HollowZeroMapEdge:

    def __init__(self, node_1: HollowZeroMapNode, node_2: HollowZeroMapNode):
        self.node_1: HollowZeroMapNode = node_1
        self.node_2: HollowZeroMapNode = node_2


class HollowZeroMap:

    def __init__(self, nodes: List[HollowZeroMapNode],
                 current_idx: int,
                 edges: dict[int, List[int]]):
        self.nodes: List[HollowZeroMapNode] = nodes
        self.current_idx: int = current_idx
        self.edges: dict[int, List[int]] = edges
