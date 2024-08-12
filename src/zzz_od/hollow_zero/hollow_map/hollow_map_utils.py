from cv2.typing import MatLike
from typing import List, Optional

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils import cal_utils
from zzz_od.hollow_zero.hollow_map.hollow_zero_map import HollowZeroMap, HollowZeroMapNode
from zzz_od.yolo.detect_utils import DetectFrameResult


def construct_map_from_yolo_result(detect_results: List[DetectFrameResult]) -> Optional[HollowZeroMap]:
    nodes: List[HollowZeroMapNode] = []

    for detect_result in detect_results:
        for result in detect_result.results:
            pos = Rect(result.x1, result.y1, result.x2, result.y2)

            # 先判断与已有的节点是否重复
            is_new = True
            for existed in nodes:
                if cal_utils.distance_between(pos.center, existed.pos.center) < 50:
                    is_new = False
                    break
            if not is_new:
                continue

            node = HollowZeroMapNode(pos, result.detect_class.class_name[5:])
            nodes.append(node)

    current_idx: Optional[int] = None
    for i in range(len(nodes)):
        if nodes[i].node_name == '当前':
            current_idx = i
    if current_idx is None:
        return None

    edges: dict[int, List[int]] = {}

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            node_1 = nodes[i]
            node_2 = nodes[j]

            if _at_left(node_1, node_2): # 1在2左边
                _add_edge(edges, i, j)
            elif _at_right(node_1, node_2): # 1在2右边
                _add_edge(edges, i, j)
            elif _above(node_1, node_2): # 1在2上边
                _add_edge(edges, i, j)
            elif _under(node_1, node_2): # 1在2下边
                _add_edge(edges, i, j)

    return HollowZeroMap(nodes, current_idx, edges)


def _at_left(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2左边
    :param node_1:
    :param node_2:
    :return:
    """
    return abs(node_1.pos.x2 - node_2.pos.x1) <= 10 and _is_same_row(node_1, node_2)

def _at_right(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2右边
    :param node_1:
    :param node_2:
    :return:
    """
    return abs(node_1.pos.x1 - node_2.pos.x2) <= 10 and _is_same_row(node_1, node_2)

def _above(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2上边
    :param node_1:
    :param node_2:
    :return:
    """
    return abs(node_1.pos.y2 - node_2.pos.y1) <= 10 and _is_same_col(node_1, node_2)

def _under(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2上边
    :param node_1:
    :param node_2:
    :return:
    """
    return abs(node_1.pos.y1 - node_2.pos.y2) <= 10 and _is_same_col(node_1, node_2)

def _is_same_row(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    y1_close = abs(node_1.pos.y1 - node_2.pos.y1) <= 20
    y2_close = abs(node_1.pos.y2 - node_2.pos.y2) <= 20
    return y1_close or y2_close


def _is_same_col(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    x1_close = abs(node_1.pos.x1 - node_2.pos.x1) <= 20
    x2_close = abs(node_1.pos.x2 - node_2.pos.x2) <= 20
    return x1_close or x2_close


def _add_edge(edges: dict[int, List[int]], x: int, y: int) -> None:
    _add_directed_edge(edges, x, y)
    _add_directed_edge(edges, y, x)


def _add_directed_edge(edges: dict[int, List[int]], x: int, y: int) -> None:
    if x not in edges:
        edges[x] = [y]
    else:
        edges[x].append(y)


def draw_map(screen: MatLike, current_map: HollowZeroMap,
             next_node: Optional[HollowZeroMapNode] = None) -> MatLike:
    """
    在图上画出地图
    :param screen:
    :param current_map:
    :return:
    """
    import cv2
    to_draw = screen.copy()

    for node in current_map.nodes:
        cv2.rectangle(to_draw, (node.pos.x1, node.pos.y1), (node.pos.x2, node.pos.y2), (255, 0, 0), 2)

    for i, j_list in current_map.edges.items():
        for j in j_list:
            if j > i:
                node_1 = current_map.nodes[i]
                node_2 = current_map.nodes[j]
                cv2.line(to_draw, node_1.pos.center.tuple(), node_2.pos.center.tuple(),
                         (0, 255, 0), 2)

    if next_node is not None:
        cv2.circle(to_draw, next_node.pos.center.tuple(), 20, (0, 0, 255), 2)

    return to_draw


class RouteSearchRoute:

    def __init__(self, node: HollowZeroMapNode, node_idx: int, first_step: int, step_cnt: int, distance: float):
        self.node: HollowZeroMapNode = node  # 需要前往的节点
        self.node_idx: int = node_idx  # 需要前往的节点的下标
        self.first_step: int = first_step  # 第一步需要走的节点下标
        self.step_cnt: int = step_cnt  # 走到这个格子需要的步数
        self.distance: float = distance  # 需要前往的节点的距离


def search_map(current_map: HollowZeroMap) -> dict[int, RouteSearchRoute]:
    """
    对当前地图进行搜索 获取前往每个节点的路径
    :param current_map:
    :return:
    """
    result: dict[int, RouteSearchRoute] = {}

    if current_map is None or current_map.current_idx is None:
        return result

    current_idx = current_map.current_idx
    current_node = current_map.nodes[current_idx]
    current_route = RouteSearchRoute(current_node, current_idx, current_idx, 0, 0)
    result[current_idx] = current_route

    if current_idx not in current_map.edges:
        return result

    searched: set[int] = set()  # 已经搜索过的
    searched.add(current_idx)

    bfs_queue: List[RouteSearchRoute] = [current_route]
    bfs_idx: int = 0
    while bfs_idx < len(bfs_queue):
        current = bfs_queue[bfs_idx]
        current_node_idx = current.node_idx
        bfs_idx += 1

        if current_node_idx not in current_map.edges:  # 没有边
            continue

        for next_idx in current_map.edges[current_node_idx]:
            if next_idx in searched:
                continue
            next_node = current_map.nodes[next_idx]
            next_entry = next_node.entry

            next_route = RouteSearchRoute(
                node=next_node,
                node_idx=next_idx,
                first_step=next_idx if current.first_step == current_idx else current.first_step,
                step_cnt=current.step_cnt + (next_entry.need_step if next_entry is not None else 1),
                distance=cal_utils.distance_between(current_node.pos.center, next_node.pos.center)
            )
            bfs_queue.append(next_route)
            searched.add(next_idx)
            result[next_idx] = next_route

    return result


def get_route_in_1_step_benefit(idx_2_route: dict[int, RouteSearchRoute]) -> Optional[RouteSearchRoute]:
    """
    获取1步能到的奖励节点的路径
    :param idx_2_route:
    :return:
    """
    target: Optional[RouteSearchRoute] = None
    for idx, route in idx_2_route.items():
        if route.step_cnt != 1:
            continue
        entry = route.node.entry
        if entry is None or not entry.is_benefit:
            continue

        if target is None or target.distance > route.distance:
            target = route

    return target


def get_route_by_entry(idx_2_route: dict[int, RouteSearchRoute], entry_name: str) -> Optional[RouteSearchRoute]:
    """
    根据格子类型找最近能到的路径
    :param idx_2_route:
    :return:
    """
    target: Optional[RouteSearchRoute] = None
    for idx, route in idx_2_route.items():
        entry = route.node.entry
        if entry is None or entry.entry_name != entry_name:
            continue

        if (target is None
                or target.step_cnt > route.step_cnt
                or (target.step_cnt == route.step_cnt and target.distance > route.distance)):
            target = route

    return target


def get_route_by_direction(idx_2_route: dict[int, RouteSearchRoute], direction: str) -> Optional[RouteSearchRoute]:
    """
    根据方向找最远能到达的路径
    :param idx_2_route:
    :return:
    """
    target: Optional[RouteSearchRoute] = None
    for idx, route in idx_2_route.items():
        if target is None:
            target = route
        elif direction == 'w' and target.node.pos.y1 > route.node.pos.y1:
            target = route
        elif direction == 's' and target.node.pos.y2 < route.node.pos.y2:
            target = route
        elif direction == 'a' and target.node.pos.x1 > route.node.pos.x1:
            target = route
        elif direction == 'd' and target.node.pos.x2 < route.node.pos.x2:
            target = route

    return target
