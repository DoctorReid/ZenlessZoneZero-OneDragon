from typing import List

from zzz_od.hollow_zero.game_data.hollow_zero_resonium import Resonium


def choose_resonium_by_priority(item_list: List[Resonium], priority_list: List[str]):
    """
    按优先级 找出第一个
    :param item_list:
    :param priority_list:
    :return:
    """
    # 先按等级排序
    level_list: List[Resonium] = []
    for level in ['S', 'A', 'B', '']:
        for i in item_list:
            if i.level == level:
                level_list.append(i)

    idx_list: List[int] = []  # 最终的下标排序结果
    for priority_item in priority_list:
        for i in range(len(level_list)):
            if i in idx_list:
                continue
            item = level_list[i]
            if item.category == priority_item:  # 分类符合
                idx_list.append(i)
                break

            if item.name == priority_item:  # 名称符合
                idx_list.append(i)
                break

    # 不符合优先级的
    for i in range(len(level_list)):
        if i not in idx_list:
            idx_list.append(i)

    return idx_list
