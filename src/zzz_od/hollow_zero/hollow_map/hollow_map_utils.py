from typing import List, Optional

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils import cal_utils
from one_dragon.yolo.detect_utils import DetectFrameResult
from zzz_od.context.zzz_context import ZContext
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroEntry
from zzz_od.hollow_zero.hollow_map.hollow_zero_map import HollowZeroMap, HollowZeroMapNode


def construct_map_from_yolo_result(
        ctx: ZContext,
        detect_result: DetectFrameResult,
        name_2_entry: dict[str, HollowZeroEntry]
) -> HollowZeroMap:
    """
    根据识别结果构造地图
    """
    nodes: List[HollowZeroMapNode] = []
    unknown = name_2_entry['未知']

    for result in detect_result.results:
        entry_name = result.detect_class.class_name[5:]
        if entry_name in name_2_entry:
            entry = name_2_entry[entry_name]
        else:
            entry = unknown

        width = result.x2 - result.x1
        height = result.y2 - result.y1
        if entry.is_base:
            pos = Rect(result.x1, result.y2 - width, result.x2, result.y2)
        else:
            pos = Rect(result.x1, result.y1, result.x2, result.y2 + height // 3)

        # 判断与已有的节点是否重复
        to_merge: Optional[HollowZeroMapNode] = None
        for existed in nodes:
            min_dis = min(pos.height, pos.width, existed.pos.height, existed.pos.width) // 2
            if cal_utils.distance_between(pos.center, existed.pos.center) < min_dis:
                to_merge = existed
                break

        if to_merge is not None:
            if to_merge.entry.is_base and not entry.is_base:  # 旧的是底座 那么将新的类型赋值上去
                to_merge.entry = entry
                to_merge.pos.y1 = pos.y1  # 使用具体类型的坐标
            elif not to_merge.entry.is_base and entry.is_base:  # 旧的是格子类型 那么把底座的范围赋值上去
                to_merge.pos.x1 = pos.x1
                to_merge.pos.x2 = pos.x2
                to_merge.pos.y2 = pos.y2
            else:
                pass
        else:
            node = HollowZeroMapNode(pos, entry,
                                     check_time=detect_result.run_time,
                                     confidence=result.score)
            nodes.append(node)

    for node in nodes:
        if node.entry.is_base:  # 只识别到底座的 赋值为未知
            node.entry = unknown

    return construct_map_from_nodes(ctx, nodes, detect_result.run_time)


def construct_map_from_nodes(
        ctx: ZContext,
        nodes: List[HollowZeroMapNode],
        check_time: float
) -> HollowZeroMap:
    current_idx: Optional[int] = None
    for i in range(len(nodes)):
        if nodes[i].entry.entry_name == '当前':
            current_idx = i

    edges: dict[int, List[int]] = {}

    for i in range(len(nodes)):
        node_1 = nodes[i]
        if (node_1.pos.x1 < 0
                or node_1.pos.y1 < 0
                or node_1.pos.x2 >= ctx.project_config.screen_standard_width
                or node_1.pos.y2 >= ctx.project_config.screen_standard_height
        ):
            continue

        for j in range(len(nodes)):
            node_2 = nodes[j]
            if (node_2.pos.x1 < 0
                    or node_2.pos.y1 < 0
                    or node_2.pos.x2 >= ctx.project_config.screen_standard_width
                    or node_2.pos.y2 >= ctx.project_config.screen_standard_height
            ):
                continue

            if not node_1.entry.can_go or not node_2.entry.can_go:
                continue

            if _at_left(node_1, node_2):  # 1在2左边
                if node_2.entry.entry_name in ['轨道-左']:
                    pass
                elif node_1.entry.entry_name in ['轨道-上', '轨道-下', '轨道-左']:
                    pass
                else:
                    _add_directed_edge(edges, i, j)
            elif _at_right(node_1, node_2):  # 1在2右边
                if node_2.entry.entry_name in ['轨道-右']:
                    pass
                elif node_1.entry.entry_name in ['轨道-上', '轨道-下', '轨道-右']:
                    pass
                else:
                    _add_directed_edge(edges, i, j)
            elif _above(node_1, node_2):  # 1在2上边
                if node_2.entry.entry_name in ['轨道-上']:
                    pass
                elif node_1.entry.entry_name in ['轨道-左', '轨道-右', '轨道-上']:
                    pass
                else:
                    _add_directed_edge(edges, i, j)
            elif _under(node_1, node_2):  # 1在2下边
                if node_2.entry.entry_name in ['轨道-下']:
                    pass
                elif node_1.entry.entry_name in ['轨道-左', '轨道-右', '轨道-下']:
                    pass
                else:
                    _add_directed_edge(edges, i, j)

    return HollowZeroMap(nodes, current_idx, edges, check_time=check_time)


def _at_left(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2左边
    :param node_1:
    :param node_2:
    :return:
    """
    min_width = min(node_1.pos.width,  node_2.pos.width) // 4
    return abs(node_1.pos.x2 - node_2.pos.x1) <= min_width and _is_same_row(node_1, node_2)


def _at_right(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2右边
    :param node_1:
    :param node_2:
    :return:
    """
    min_width = min(node_1.pos.width,  node_2.pos.width) // 4
    return abs(node_1.pos.x1 - node_2.pos.x2) <= min_width and _is_same_row(node_1, node_2)


def _above(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2上边
    :param node_1:
    :param node_2:
    :return:
    """
    min_height = min(node_1.pos.height,  node_2.pos.height) // 4
    return abs(node_1.pos.y2 - node_2.pos.y1) <= min_height and _is_same_col(node_1, node_2)


def _under(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2上边
    :param node_1:
    :param node_2:
    :return:
    """
    min_height = min(node_1.pos.height,  node_2.pos.height) // 4
    return abs(node_1.pos.y1 - node_2.pos.y2) <= min_height and _is_same_col(node_1, node_2)


def _is_same_row(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    min_height = min(node_1.pos.height,  node_2.pos.height) // 3
    y1_close = abs(node_1.pos.y1 - node_2.pos.y1) <= min_height
    y2_close = abs(node_1.pos.y2 - node_2.pos.y2) <= min_height
    return y1_close or y2_close


def _is_same_col(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    min_width = min(node_1.pos.width,  node_2.pos.width) // 3
    x1_close = abs(node_1.pos.x1 - node_2.pos.x1) <= min_width
    x2_close = abs(node_1.pos.x2 - node_2.pos.x2) <= min_width
    return x1_close or x2_close


def _add_edge(edges: dict[int, List[int]], x: int, y: int) -> None:
    _add_directed_edge(edges, x, y)
    _add_directed_edge(edges, y, x)


def _add_directed_edge(edges: dict[int, List[int]], x: int, y: int) -> None:
    if x not in edges:
        edges[x] = [y]
    else:
        edges[x].append(y)


def merge_map(ctx: ZContext, map_list: List[HollowZeroMap]):
    """
    将多个地图合并成一个
    """
    nodes: List[HollowZeroMapNode] = []
    max_check_time: Optional[float] = None

    # 每个地图的节点取出来后去重合并
    for m in map_list:
        for node in m.nodes:
            to_merge: Optional[HollowZeroMapNode] = None
            for existed in nodes:
                if cal_utils.distance_between(node.pos.center, existed.pos.center) < 100:
                    to_merge = existed
                    break

            if to_merge is not None:
                if to_merge.entry.is_base:  # 旧的是底座 那么将新的类型赋值上去
                    to_merge.entry = node.entry
                elif node.entry.is_base:  # 旧的是格子类型 新的是底座 将底座范围赋值上去
                    to_merge.pos = node.pos
                elif to_merge.entry.entry_name == '未知' and node.entry.entry_name != '未知':  # 新旧都是格子类型 旧的是未知 将新的类型赋值上去
                    to_merge.entry = node.entry
                elif to_merge.entry.entry_name != '未知' and node.entry.entry_name == '未知':  # 新旧都是格子类型 新的是未知 保持不变
                    pass
                elif to_merge.confidence < node.confidence:  # 新旧都是格子类型 旧的识别置信度低 将新的类型赋值上去
                    to_merge.entry = node.entry
                elif to_merge.check_time < node.check_time:  # 新旧都是格子类型 新的识别时间更晚 将新的类型赋值上去
                    to_merge.entry = node.entry
            else:
                nodes.append(node)

        if max_check_time is None or m.check_time > max_check_time:
            max_check_time = m.check_time

    return construct_map_from_nodes(ctx, nodes, max_check_time)
