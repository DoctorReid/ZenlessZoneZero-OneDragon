import cv2
import numpy as np
from cv2.typing import MatLike
from typing import Optional

from one_dragon.utils import cv2_utils
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import AgentStateDef


def get_template(ctx: ZContext, state_def: AgentStateDef,
                 total: Optional[int] = None, pos: Optional[int] = None):
    """
    获取对应的角色状态模版
    :param ctx: 上下文
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置
    :return:
    """
    if total is None or pos is None:
        template_id = state_def.template_id
    else:
        if total == 2 and pos == 2:  # 只有22位置比较特殊
            template_id = ('%s_%d_%d' % (state_def.template_id, total, pos))
        else:
            template_id = ('%s_%d_%d' % (state_def.template_id, 3, pos))
    template = ctx.template_loader.get_template('agent_state', template_id)
    return template


def check_cnt_by_color_range(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef,
        total: Optional[int] = None,
        pos: Optional[int] = None
) -> int:
    """
    在指定区域内，按颜色判断连通块有多少个
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置
    :return:
    """
    template = get_template(ctx, state_def, total, pos)
    if template is None:
        return 0
    part = cv2_utils.crop_image_only(screen, template.get_template_rect_by_point())
    to_check = cv2.bitwise_and(part, part, mask=template.mask)

    mask = cv2.inRange(to_check, state_def.lower_color, state_def.upper_color)
    mask = cv2_utils.dilate(mask, 2)
    # cv2_utils.show_image(mask, wait=0)

    # 查找连通区域
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

    # 统计连通区域数量
    count = 0
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= state_def.connect_cnt:
            count += 1

    return count


def check_exist_by_color_range(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef,
        total: Optional[int] = None,
        pos: Optional[int] = None
) -> bool:
    """
    在指定区域内，按颜色判断是否有出现
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置
    """
    cnt = check_cnt_by_color_range(ctx, screen, state_def, total, pos)
    return cnt > 0


def check_length_by_background_gray(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef,
        total: Optional[int] = None,
        pos: Optional[int] = None
) -> int:
    """
    在指定区域内，按背景的灰度色来反推横条的长度
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置
    :return: 0~100
    """
    template = get_template(ctx, state_def, total, pos)
    if template is None:
        return 0
    part = cv2_utils.crop_image_only(screen, template.get_template_rect_by_point())
    # 模版需要保证高度是1
    to_check = part

    gray = cv2.cvtColor(to_check, cv2.COLOR_RGB2GRAY).mean(axis=0)
    mask = (gray >= state_def.lower_color) & (gray <= state_def.upper_color)
    bg_mask_idx = np.where(mask)
    fg_mask_idx = np.where(~mask)
    total_cnt = len(gray)

    bg_left = np.min(bg_mask_idx, initial=total_cnt+1)
    bg_right = np.max(bg_mask_idx, initial=0)

    lg_left = np.min(fg_mask_idx, initial=total_cnt+1)
    lg_right = np.max(fg_mask_idx, initial=0)

    # 有一些条 中间是有分隔的 这部分有可能被认为前景色
    # 所以如果前景色的左边如果能找到背景色 说明这个是分隔条
    if bg_left < lg_left:  # 用背景色来判断长度
        bg_cnt = bg_right - bg_left + 1

        if bg_cnt < 0:
            bg_cnt = 0
        if bg_cnt > total_cnt:
            bg_cnt = total_cnt

        fg_cnt = total_cnt - bg_cnt
    else:  # 用前景色来判断长度
        fg_cnt = lg_right - lg_left + 1

        if fg_cnt < 0:
            fg_cnt = 0
        if fg_cnt > total_cnt:
            fg_cnt = total_cnt

    return int(fg_cnt * 100.0 / total_cnt)


def check_length_by_foreground_gray(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef,
        total: Optional[int] = None,
        pos: Optional[int] = None
) -> int:
    """
    在指定区域内，按背景的灰度色来反推横条的长度
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置
    :return: 0~100
    """
    template = get_template(ctx, state_def, total, pos)
    if template is None:
        return 0
    part = cv2_utils.crop_image_only(screen, template.get_template_rect_by_point())
    # 模版需要保证高度是1
    gray = cv2.cvtColor(part, cv2.COLOR_RGB2GRAY).mean(axis=0)
    if state_def.split_color_range is not None:
        split_mask = (gray >= state_def.split_color_range[0]) & (gray <= state_def.split_color_range[1])
        gray = gray[np.where(split_mask == False)]

    mask = (gray >= state_def.lower_color) & (gray <= state_def.upper_color)
    mask_idx = np.where(mask)
    total_cnt = len(gray)

    left = np.min(mask_idx, initial=total_cnt+1)
    right = np.max(mask_idx, initial=0)
    fg_cnt = right - left + 1

    if fg_cnt < 0:
        fg_cnt = 0
    if fg_cnt > total_cnt:
        fg_cnt = total_cnt

    return int(fg_cnt * state_def.max_length / total_cnt)


def check_length_by_foreground_color(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef,
        total: Optional[int] = None,
        pos: Optional[int] = None
) -> int:
    """
    在指定区域内，按前景色(彩色)来计算横条的长度
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置
    :return: 0~100
    """
    template = get_template(ctx, state_def, total, pos)
    if template is None:
        return 0
    part = cv2_utils.crop_image_only(screen, template.get_template_rect_by_point())
    to_check = part

    mask = cv2.inRange(to_check, state_def.lower_color, state_def.upper_color)
    fg_cnt = np.sum(mask == 255)
    total_cnt = mask.shape[1]

    return int(fg_cnt * 100.0 / total_cnt)
