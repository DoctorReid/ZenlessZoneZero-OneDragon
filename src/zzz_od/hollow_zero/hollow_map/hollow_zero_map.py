import time

from typing import List, Optional

from one_dragon.base.geometry.rectangle import Rect
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroEntry


class HollowZeroMapNode:

    def __init__(self, pos: Rect, entry: HollowZeroEntry,
                 check_time: Optional[float] = None,
                 confidence: float = 0):
        self.pos: Rect = pos
        self.entry: HollowZeroEntry = entry
        self.check_time: float = time.time() if check_time is None else check_time  # 识别时间
        self.confidence: float = confidence


class HollowZeroMapEdge:

    def __init__(self, node_1: HollowZeroMapNode, node_2: HollowZeroMapNode):
        self.node_1: HollowZeroMapNode = node_1
        self.node_2: HollowZeroMapNode = node_2


class HollowZeroMap:

    def __init__(self, nodes: List[HollowZeroMapNode],
                 current_idx: int,
                 edges: dict[int, List[int]],
                 check_time: Optional[float] = None):
        self.nodes: List[HollowZeroMapNode] = nodes
        self.current_idx: int = current_idx
        self.edges: dict[int, List[int]] = edges
        self.check_time: float = time.time() if check_time is None else check_time  # 识别时间

    def contains_entry(self, entry_name: str) -> bool:
        """
        是否保护某个类型的格子
        :param entry_name:
        :return:
        """
        for node in self.nodes:
            if node.entry.entry_name == entry_name:
                return True

        return False
