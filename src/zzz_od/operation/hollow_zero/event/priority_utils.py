from typing import List

from zzz_od.hollow_zero.game_data.hollow_zero_resonium import Resonium


def choose_resonium_by_priority(item_list: List[Resonium], priority_list: List[str]):
    """
    按优先级 找出第一个
    :param item_list:
    :param priority_list:
    :return:
    """
    idx_list: List[int] = []  # 最终的下标排序结果
    for priority_item in priority_list:
        for i in range(len(item_list)):
            if i in idx_list:
                continue
            item = item_list[i]
            if item.category == priority_item:

