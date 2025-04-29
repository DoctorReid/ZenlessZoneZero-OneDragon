import cv2
import difflib
from typing import Optional, List

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.compendium import CompendiumMissionType
from zzz_od.operation.zzz_operation import ZOperation


class CompendiumChooseMissionType(ZOperation):
    """
    快捷手册中选择特定副本类型的操作类
    """

    def __init__(self, ctx: ZContext, mission_type: CompendiumMissionType):
        """
        已经打开了快捷手册了 选择了 Tab 和 分类
        目标是 选择一个关卡传送 点击传送后 不会等待画面加载
        :param ctx:
        """
        ZOperation.__init__(
            self, ctx,
            op_name='%s %s %s' % (
                gt('快捷手册'),
                gt('选择副本类型'),
                gt(mission_type.mission_type_name)
            )
        )

        self.mission_type: CompendiumMissionType = mission_type

    @operation_node(name='选择副本', is_start_node=True, node_max_retry_times=20)
    def choose_tab(self) -> OperationRoundResult:
        if self.mission_type.mission_type_name == "代理人方案培养":
            return self.handle_agent_training()

        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('快捷手册', '副本列表')
        part = cv2_utils.crop_image_only(screen, area.rect)

        mission_type_list: List[CompendiumMissionType] = self.ctx.compendium_service.get_same_category_mission_type_list(self.mission_type.mission_type_name)
        if mission_type_list is None:
            return self.round_fail('非法的副本分类 %s' % self.mission_type.mission_type_name)

        before_target_cnt: int = 0  # 在目标副本前面的数量
        target_idx: int = -1
        target_list = []
        for idx, mission_type in enumerate(mission_type_list):
            if mission_type.mission_type_name == self.mission_type.mission_type_name:
                target_idx = idx
            target_list.append(gt(mission_type.mission_type_name))

        if target_idx == -1:
            return self.round_fail('非法的副本分类 %s' % self.mission_type.mission_type_name)

        target_point: Optional[Point] = None
        ocr_results = self.ctx.ocr.run_ocr(part)
        for ocr_result, mrl in ocr_results.items():
            if mrl.max is None:
                continue

            results = difflib.get_close_matches(ocr_result, target_list, n=1)

            if results is None or len(results) == 0:
                continue

            idx = target_list.index(results[0])
            if idx == target_idx:
                target_point = area.left_top + mrl.max
                break
            elif idx < target_idx:
                before_target_cnt += 1

        if target_point is None:
            return self.handle_scroll(area, before_target_cnt)

        return self.handle_go_button(screen, target_point)

    def handle_agent_training(self) -> OperationRoundResult:
        """
        专门处理"代理人方案培养"副本的方法
        """
        log.debug("开始处理代理人方案培养副本")

        # 1. 截取当前屏幕
        screen = self.screenshot()

        # 2. 获取代理人方案培养的特殊区域
        area = self.ctx.screen_loader.get_area("快捷手册", "目标列表")

        # 3. 裁剪出区域图像
        part = cv2_utils.crop_image_only(screen, area.rect)

        # 4. 转换到HSV色彩空间并过滤低饱和度和色调值
        hsv = cv2.cvtColor(part, cv2.COLOR_BGR2HSV)
        # 创建掩码：H和S都小于10的像素
        mask = cv2.inRange(hsv, (0, 0, 0), (10, 10, 255))
        # 反转掩码（保留非黑灰色区域）
        binary = cv2.bitwise_not(mask)

        # 5. 查找所有连通区域并过滤小面积区域
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        # 过滤掉面积小于800的连通区域
        min_area = 800  # 最小有效区域面积
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= min_area]

        for i, cnt in enumerate(contours):
            x, y, w, h = cv2.boundingRect(cnt)
            log.debug(
                f"目标代理人头像{i}: x={x}, y={y}, 宽={w}, 高={h}, 面积={cv2.contourArea(cnt)}"
            )

        # 6. 过滤并找到一个有效区域
        target_point = None
        if contours and len(contours) > 0:
            x, y, w, h = cv2.boundingRect(contours[0])
            target_point = area.left_top + Point(
                x + w // 2, y + h // 2 - 80
            )  # 减去80是为了确保能找到前往

        # 7. 如果没有找到有效区域，执行滑动操作
        if target_point is None:
            log.debug("未找到有效区域，执行滑动操作")
            return self.handle_scroll(area, 1)

        log.debug(f"最终目标点: {target_point}")
        return self.handle_go_button(screen, target_point)

    def handle_scroll(
        self, area: Rect, before_target_cnt: int = 0
    ) -> OperationRoundResult:
        """
        处理滑动操作
        """
        if before_target_cnt > 0:
            dy = -1
        else:
            dy = 1

        # 部分特殊类型的副本 外面的顺序和里面的顺序反转
        if self.mission_type.category.category_name in ['定期清剿', '专业挑战室', '恶名狩猎']:
                dy = dy * -1

        # 滑动
        start = area.center
        end = start + Point(0, 300 * dy)
        self.ctx.controller.drag_to(start=start, end=end)
        return self.round_retry(status='找不到 %s' % self.mission_type.mission_type_name, wait=1)

    def handle_go_button(self, screen, target_point: Point) -> OperationRoundResult:
        """
        处理前往按钮点击逻辑
        """
        area = self.ctx.screen_loader.get_area('快捷手册', '前往列表')
        go_rect = area.rect
        part = cv2_utils.crop_image_only(screen, go_rect)
        ocr_results = self.ctx.ocr.run_ocr(part)

        target_go_point: Optional[Point] = None
        for ocr_result, mrl in ocr_results.items():
            if mrl.max is None:
                continue
            if not str_utils.find_by_lcs(gt('前往'), ocr_result, percent=0.5):
                continue
            for mr in mrl:
                go_point = go_rect.left_top + mr.center
                if go_point.y <= target_point.y:
                    continue
                if target_go_point is None or go_point.y < target_go_point.y:
                    target_go_point = go_point

        if target_go_point is None:
            # 出现了副本名称 但没有出现前往 前往一定在下方 固定往下滑动即可
            start = area.center
            end = start + Point(0, -200)
            self.ctx.controller.drag_to(start=start, end=end)
            return self.round_retry(status='找不到 %s' % '前往', wait=1)

        click = self.ctx.controller.click(target_go_point)
        return self.round_success(wait=1)

    @node_from(from_name='选择副本')
    @operation_node(name='确认')
    def confirm(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '快捷手册', '传送确认',
                                                 success_wait=5, retry_wait=1)


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.start_running()
    target = ctx.compendium_service.get_mission_type_data('训练', '定期清剿', '高塔与巨炮')
    op = CompendiumChooseMissionType(ctx, target)
    op.execute()


if __name__ == '__main__':
    __debug()
