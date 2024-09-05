import cv2
import numpy as np
from cv2.typing import MatLike

from one_dragon.utils import cv2_utils
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import AgentStateDef, AgentEnum


def check_cnt_by_color_range(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef
) -> int:
    """
    在指定区域内，按颜色判断连通块有多少个
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :return:
    """
    area = ctx.screen_loader.get_area('角色状态', state_def.state_name)
    part = cv2_utils.crop_image_only(screen, area.rect)
    if area.template_id is not None and len(area.template_id) > 0:
        part_mask = ctx.template_loader.get_template_mask(area.template_sub_dir, area.template_id)
        print(part.shape)
        print(part_mask.shape)
        to_check = cv2.bitwise_and(part, part, mask=part_mask)
    else:
        to_check = part

    mask = cv2.inRange(to_check, state_def.lower_color, state_def.upper_color)
    # cv2_utils.show_image(mask, wait=0)

    # 查找连通区域
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

    # 统计连通区域数量
    count = 0
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] > state_def.connect_cnt:
            count += 1

    return count


def check_exist_by_color_range(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef
) -> bool:
    """
    在指定区域内，按颜色判断是否有出现
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    """
    cnt = check_cnt_by_color_range(ctx, screen, state_def)
    return cnt > 0


def check_length_by_background(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef
) -> int:
    """
    在指定区域内，按背景色(黑色)来反推横条的长度
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :return: 0~100
    """
    area = ctx.screen_loader.get_area('角色状态', state_def.state_name)
    part = cv2_utils.crop_image_only(screen, area.rect)
    to_check = part

    gray = cv2.cvtColor(to_check, cv2.COLOR_RGB2GRAY).mean(axis=0)
    bg_cnt = np.sum((gray >= state_def.lower_color) & (gray <= state_def.upper_color))
    total_cnt = len(gray)

    return 100 - int(bg_cnt * 100.0 / total_cnt)


def check_length_by_color_range(
        ctx: ZContext,
        screen: MatLike,
        state_def: AgentStateDef
) -> int:
    """
    在指定区域内，按背景色(黑色)来反推横条的长度
    :param ctx: 上下文
    :param screen: 游戏画面
    :param state_def: 角色状态定义
    :return: 0~100
    """
    area = ctx.screen_loader.get_area('角色状态', state_def.state_name)
    part = cv2_utils.crop_image_only(screen, area.rect)
    to_check = part

    mask = cv2.inRange(to_check, state_def.lower_color, state_def.upper_color)

    bg_cnt = np.sum(mask == 255)
    total_cnt = mask.shape[1]

    return int(bg_cnt * 100.0 / total_cnt)


def __debug_zhu_yuan():
    ctx = ZContext()
    ctx.init_by_config()

    from one_dragon.utils import os_utils
    import os
    agent = AgentEnum.ZHU_YUAN.value
    img_path = os.path.join(
        os_utils.get_path_under_work_dir('.debug', 'devtools', 'screen', 'agent_state'),
        f'{agent.agent_id}.png'
    )
    screen = cv2_utils.read_image(img_path)
    for state in agent.state_list:
        import time
        t1 = time.time()
        print(check_cnt_by_color_range(ctx, screen, state))
        print(time.time() - t1)


def __debug_qingyi():
    ctx = ZContext()
    ctx.init_by_config()

    from one_dragon.utils import os_utils
    import os
    agent = AgentEnum.QINGYI.value
    for i in ['0', 'x', '100']:
        img_path = os.path.join(
            os_utils.get_path_under_work_dir('.debug', 'devtools', 'screen', 'agent_state'),
            f'{agent.agent_id}_{i}.png'
        )
        screen = cv2_utils.read_image(img_path)
        for state in agent.state_list:
            print(check_length_by_background(ctx, screen, state))


if __name__ == '__main__':
    __debug_qingyi()