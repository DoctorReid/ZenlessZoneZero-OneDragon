from cv2.typing import MatLike
from typing import List

from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.hollow_zero.game_data.hollow_zero_resonium import Resonium


def get_to_choose_list(ctx: ZContext, screen: MatLike, target_cn: str, target_lcs_percent: float = 1) -> List[MatchResult]:
    """
    识别画面上的鸣徽
    :param screen:
    :param target_cn:
    :return: 按钮的位置 + data=对应鸣徽
    """
    result_list: List[MatchResult] = []

    for i in range(1, 4):
        name_area = ctx.screen_loader.get_area('零号空洞-事件', '鸣徽名称-%d' % i)
        confirm_area = ctx.screen_loader.get_area('零号空洞-事件', '鸣徽选择-%d' % i)

        name_full_str = ctx.ocr.run_ocr_single_line(cv2_utils.crop_image_only(screen, name_area.rect))
        confirm_str = ctx.ocr.run_ocr_single_line(cv2_utils.crop_image_only(screen, confirm_area.rect))

        if not str_utils.find_by_lcs(gt(target_cn), confirm_str, percent=target_lcs_percent):
            continue

        idx = name_full_str.find('】')
        if idx == -1:
            idx = name_full_str.find(']')
        if idx == -1:
            continue

        cate_str = name_full_str[:idx]
        name_str = name_full_str[idx+1:]
        r = ctx.hollow.data_service.match_resonium_by_ocr(cate_str, name_str)
        if r is None:
            continue

        mr = MatchResult(
            1, confirm_area.x1, confirm_area.y1, confirm_area.width, confirm_area.height,
            data=r
        )
        result_list.append(mr)

    return result_list


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
