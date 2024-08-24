import cv2
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


if __name__ == '__main__':
    __debug_zhu_yuan()