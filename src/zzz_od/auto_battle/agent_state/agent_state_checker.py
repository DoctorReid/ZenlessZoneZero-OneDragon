import cv2
import numpy as np
from cv2.typing import MatLike
from typing import Optional, Tuple, List

from one_dragon.utils import cv2_utils
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import AgentStateDef
from one_dragon.utils.log_utils import log

def get_template(ctx: ZContext, state_def: AgentStateDef,
                 total: Optional[int] = None, pos: Optional[int] = None):
    """
    获取对应的角色状态模版
    :param ctx: 上下文
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置 从1开始
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
    :param pos: 角色位置 从1开始
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
) -> int:
    """
    在指定区域内，按颜色判断是否有出现
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置 从1开始
    :return 存在返回1 不存在返回0
    """
    cnt = check_cnt_by_color_range(ctx, screen, state_def, total, pos)
    return 1 if cnt > 0 else 0


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
    :param pos: 角色位置 从1开始
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
    :param pos: 角色位置 从1开始
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
    :param pos: 角色位置 从1开始
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

    length = round(fg_cnt * 1.0 * state_def.max_length / total_cnt)
    if length > state_def.max_length:
        length = state_def.max_length
    return length


def check_template_not_found(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef,
        total: Optional[int] = None,
        pos: Optional[int] = None
) -> int:
    """
    在指定区域内，找不到对应模板
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置 从1开始
    :return: 找不到对应模板返回1 否则返回0
    """
    template = get_template(ctx, state_def, total, pos)
    if template is None:
        return False
    to_check = cv2_utils.crop_image_only(screen, template.get_template_rect_by_point())
    mrl = cv2_utils.match_template(source=to_check, template=template.raw, mask=template.mask,
                                   threshold=state_def.template_threshold)

    return 1 if mrl.max is None else 0


def check_template_found(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef,
        total: Optional[int] = None,
        pos: Optional[int] = None
) -> int:
    """
    在指定区域内，找到对应模板
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置 从1开始
    :return: 找不到对应模板返回1 否则返回0
    """
    template = get_template(ctx, state_def, total, pos)
    if template is None:
        return False
    to_check = cv2_utils.crop_image_only(screen, template.get_template_rect_by_point())
    mrl = cv2_utils.match_template(source=to_check, template=template.raw, mask=template.mask,
                                   threshold=state_def.template_threshold)

    return 1 if mrl.max is not None else 0


def check_cnt_by_color_channel_max_range(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef,
        total: Optional[int] = None,
        pos: Optional[int] = None
) -> int:
    """
    在指定区域内，按颜色通道的最大值判断连通块有多少个
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置 从1开始
    :return:
    """
    template = get_template(ctx, state_def, total, pos)
    if template is None:
        return 0
    part = cv2_utils.crop_image_only(screen, template.get_template_rect_by_point())
    to_check = cv2.bitwise_and(part, part, mask=template.mask)

    r, g, b = cv2.split(to_check)
    max_channel = np.max(np.array([r, g, b]), axis=0)
    mask = cv2.inRange(max_channel, state_def.lower_color, state_def.upper_color)
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


def check_exist_by_color_channel_max_range(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef,
        total: Optional[int] = None,
        pos: Optional[int] = None
) -> int:
    """
    在指定区域内，按颜色通道的最大值判断是否有出现
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置 从1开始
    """
    cnt = check_cnt_by_color_channel_max_range(ctx, screen, state_def, total, pos)
    return 1 if cnt > 0 else 0


def check_cnt_by_color_channel_equal_range(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef,
        total: Optional[int] = None,
        pos: Optional[int] = None
) -> int:
    # 1. 获取模板并裁剪目标区域
    template = get_template(ctx, state_def, total, pos)
    if template is None:
        return 0

    part = cv2_utils.crop_image_only(screen, template.get_template_rect_by_point())
    to_check = cv2.bitwise_and(part, part, mask=template.mask)

    # 2. 分离并检查RGB三通道
    r, g, b = cv2.split(to_check)
    # 检查每个像素点的三个通道是否完全相等
    channel_equal = (r == g) & (g == b)
    
    # 3. 统计三通道相等的点的数量
    equal_points_count = np.sum(channel_equal)
    
    # # 4. 只在点数量超过阈值时输出调试信息和保存图片
    # if equal_points_count >= state_def.connect_cnt:
    #     log.debug(f'检测到三通道相等的点数量: {equal_points_count}')
        
    #     # 保存调试图片
    #     import os
    #     from datetime import datetime
    #     debug_dir = r'E:\github\ZenlessZoneZero-OneDragon\.debug\images'
    #     os.makedirs(debug_dir, exist_ok=True)
        
    #     # 生成时间戳和文件名基础部分
    #     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    #     base_filename = f'equal_range_{equal_points_count}pts_{timestamp}'
        
    #     # 保存原始裁剪图片
    #     cv2.imwrite(os.path.join(debug_dir, f'{base_filename}_original.png'), 
    #                 cv2.cvtColor(to_check, cv2.COLOR_RGB2BGR))
        
    #     # 保存相等点的掩码图片
    #     mask = channel_equal.astype(np.uint8) * 255
    #     cv2.imwrite(os.path.join(debug_dir, f'{base_filename}_mask.png'), mask)

    # 5. 返回结果
    return 1 if equal_points_count >= state_def.connect_cnt else 0

def check_circles(
    ctx: ZContext,
    screen: MatLike,
    state_def: AgentStateDef,
    total: Optional[int] = None,
    pos: Optional[int] = None
) -> int:
    """
    在指定区域内查找指定颜色的圆形
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :param total: 总角色数量
    :param pos: 角色位置 从1开始
    :return: 找到的圆形数量
    """

    template = get_template(ctx, state_def, total, pos)
    if template is None:
        log.debug(f'准心模板获取失败')
        return 0

    # 直接从state_def.params获取参数
    params = {
        'target_color_hsv': np.array(state_def.params['color']['target_hsv']),
        'color_tolerance_hsv': np.array(state_def.params['color']['tolerance_hsv']),
        'hough_params': {
            'dp_range': state_def.params['hough'].get('dp_range', [1.0]),
            'param1_range': state_def.params['hough']['param1_range'],
            'param2_range': state_def.params['hough']['param2_range'],
            'minRadius_range': state_def.params['hough']['min_radius_range'],
            'maxRadius_range': state_def.params['hough']['max_radius_range'],
            'minDist_range': [lambda shape: shape[0]/state_def.params['hough'].get('min_dist_divisor', 8)]  # 使用配置的除数
        }
    }

    # 获取检测区域
    part = cv2_utils.crop_image_only(screen, template.get_template_rect_by_point())
    to_check = cv2.bitwise_and(part, part, mask=template.mask)

    # **立即对调颜色通道 (假设 to_check 是 RGB)**
    try:
        to_check_bgr = cv2.cvtColor(to_check, cv2.COLOR_RGB2BGR)
    except:
        to_check_bgr = to_check # 如果转换失败，则使用原始图像

    # 调用核心检测函数，传递颜色转换后的图像
    circles = _find_circles(
        roi_image=to_check_bgr,  # 传递颜色转换后的图像
        params=params,
        target_count=state_def.connect_cnt if hasattr(state_def, 'connect_cnt') else None
    )

    circle_count = len(circles)
    return 1 if circle_count > 2 else 0

# _find_circles 函数保持不变
def _find_circles(
    roi_image: np.ndarray,
    params: dict,
    target_count: Optional[int] = None
) -> List[Tuple[int, int, int]]:

    roi = roi_image
    found_circles = []

    if roi.size == 0:
        return found_circles

    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lower_bound = np.clip(params['target_color_hsv'] - params['color_tolerance_hsv'], 0, 255)
    upper_bound = np.clip(params['target_color_hsv'] + params['color_tolerance_hsv'], 0, 255)
    mask_color = cv2.inRange(hsv_roi, lower_bound, upper_bound)
    masked_roi = cv2.bitwise_and(roi, roi, mask=mask_color)
    gray_roi = cv2.cvtColor(masked_roi, cv2.COLOR_BGR2GRAY)
    blurred_roi = cv2.GaussianBlur(gray_roi, (5, 5), 0)

    hough_params = params['hough_params']
    dp_range = hough_params['dp_range']
    param1_range = hough_params['param1_range']
    param2_range = hough_params['param2_range']
    min_radius_range = hough_params['minRadius_range']
    max_radius_range = hough_params['maxRadius_range']
    min_dist_func = hough_params['minDist_range'][0] # 获取 minDist 的函数

    for dp in dp_range:
        if target_count is not None and len(found_circles) >= target_count:
            break
        for minDist in [min_dist_func(roi.shape)]: # 调用函数获取 minDist
            if target_count is not None and len(found_circles) >= target_count:
                break
            for param1 in param1_range:
                if target_count is not None and len(found_circles) >= target_count:
                    break
                for param2 in param2_range:
                    if target_count is not None and len(found_circles) >= target_count:
                        break
                    circles = cv2.HoughCircles(blurred_roi, cv2.HOUGH_GRADIENT, dp=dp, minDist=minDist,
                                                param1=param1, param2=param2,
                                                minRadius=min(min_radius_range), maxRadius=max(max_radius_range))
                    if circles is not None:
                        circles = np.round(circles[0, :]).astype("int")
                        for x, y, r in circles:
                            center_hsv = hsv_roi[y, x]
                            if cv2.inRange(np.array([[center_hsv]]), lower_bound, upper_bound)[0][0] == 255:
                                found_circles.append((x, y, r)) # 直接使用相对于 ROI 的坐标
                                if target_count is not None and len(found_circles) >= target_count:
                                    break # 达到目标数量，跳出内层循环
            if target_count is not None and len(found_circles) >= target_count:
                break # 达到目标数量，跳出中间层循环
        if target_count is not None and len(found_circles) >= target_count:
            break # 达到目标数量，跳出外层循环

    return found_circles