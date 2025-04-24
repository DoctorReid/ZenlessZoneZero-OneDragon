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
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.compendium import CompendiumMissionType
from zzz_od.operation.zzz_operation import ZOperation
from one_dragon.utils.log_utils import log


class CompendiumChooseMissionType(ZOperation):
    """
    快捷手册中选择特定副本类型的操作类
    继承自ZOperation基类，实现选择特定副本类型的操作流程
    """

    def __init__(self, ctx: ZContext, mission_type: CompendiumMissionType):
        """
        初始化方法

        参数:
            ctx: ZContext - 游戏上下文对象，包含OCR、控制器等工具
            mission_type: CompendiumMissionType - 要选择的副本类型数据对象

        说明:
            - 该操作假设快捷手册已经打开，且已选择了Tab和分类
            - 主要目标是选择一个特定副本进行传送
            - 点击传送后不会等待画面加载完成
        """
        # 调用父类初始化，设置操作名称
        ZOperation.__init__(
            self,
            ctx,
            op_name="%s %s %s"
            % (
                gt("快捷手册"),  # 操作类型
                gt("选择副本类型"),  # 操作动作
                gt(mission_type.mission_type_name),  # 目标副本类型名称
            ),
        )

        # 保存要选择的副本类型对象
        self.mission_type: CompendiumMissionType = mission_type

    @operation_node(name="选择副本", is_start_node=True, node_max_retry_times=20)
    def choose_tab(self) -> OperationRoundResult:
        """
        选择副本类型的主要操作节点

        返回:
            OperationRoundResult - 操作结果对象

        流程:
            1. 截取屏幕
            2. 获取副本列表区域
            3. 识别副本列表中的文本
            4. 匹配目标副本
            5. 处理滑动和点击逻辑
        """
        if self.mission_type.mission_type_name == "代理人方案培养":
            return self.handle_agent_training()

        # 1. 截取当前屏幕
        screen = self.screenshot()

        # 2. 获取副本列表区域
        area = self.ctx.screen_loader.get_area("快捷手册", "副本列表")

        # 3. 裁剪出副本列表区域的图像部分
        part = cv2_utils.crop_image_only(screen, area.rect)

        # 4. 获取同分类下的所有副本类型列表
        mission_type_list: List[CompendiumMissionType] = (
            self.ctx.compendium_service.get_same_category_mission_type_list(
                self.mission_type.mission_type_name
            )
        )
        if mission_type_list is None:
            return self.round_fail(
                "非法的副本分类 %s" % self.mission_type.mission_type_name
            )

        # 5. 初始化变量:
        before_target_cnt: int = 0  # 在目标副本前面的数量(用于判断是否需要滑动)
        target_idx: int = -1  # 目标副本在列表中的索引
        target_list = []  # 副本名称列表(用于OCR匹配)

        # 6. 遍历副本列表，填充target_list并记录目标索引
        for idx, mission_type in enumerate(mission_type_list):
            if mission_type.mission_type_name == self.mission_type.mission_type_name:
                target_idx = idx
            target_list.append(gt(mission_type.mission_type_name))  # 添加国际化后的名称

        # 7. 检查目标索引是否有效
        if target_idx == -1:
            return self.round_fail(
                "非法的副本分类 %s" % self.mission_type.mission_type_name
            )

        # 8. 初始化目标点变量
        target_point: Optional[Point] = None

        # 9. 运行OCR识别副本列表区域的文本
        ocr_results = self.ctx.ocr.run_ocr(part)

        # 10. 遍历OCR结果，匹配目标副本
        for ocr_result, mrl in ocr_results.items():
            # 跳过无效的OCR结果
            if mrl.max is None:
                continue

            # 11. 使用模糊匹配找到最相似的副本名称
            results = difflib.get_close_matches(ocr_result, target_list, n=1)

            # 跳过无匹配结果
            if results is None or len(results) == 0:
                continue

            # 12. 获取匹配到的副本索引
            idx = target_list.index(results[0])

            # 13. 如果是目标副本，记录点击位置
            if idx == target_idx:
                target_point = area.left_top + mrl.max
                break
            # 14. 如果是目标之前的副本，增加计数(用于滑动判断)
            elif idx < target_idx:
                before_target_cnt += 1

        # 15. 如果未找到目标副本点，执行滑动操作
        if target_point is None:
            return self.handle_scroll(area, before_target_cnt)

        return self.handle_go_button(screen, target_point)

    def handle_agent_training(self) -> OperationRoundResult:
        """
        专门处理"代理人方案培养"副本的方法

        返回:
            OperationRoundResult - 操作结果对象
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
            return self.handle_scroll(area)

        log.debug(f"最终目标点: {target_point}")
        return self.handle_go_button(screen, target_point)

    def handle_scroll(
        self, area: Rect, before_target_cnt: int = 0
    ) -> OperationRoundResult:
        """
        处理滑动操作的独立方法

        参数:
            area: 滑动区域
            before_target_cnt: 目标前的副本数量(用于判断滑动方向)

        返回:
            OperationRoundResult - 操作结果对象
        """
        # 确定滑动方向:
        # - 如果前面有副本，说明目标在下方，向下滑动
        # - 否则向上滑动
        if before_target_cnt > 0:
            dy = -1  # 向下滑动
        else:
            dy = 1  # 向上滑动

        # 处理特殊分类的副本顺序反转问题
        # 这些分类的副本顺序与常规顺序相反
        if self.mission_type.category.category_name in [
            "定期清剿",
            "专业挑战室",
            "恶名狩猎",
        ]:
            dy = dy * -1  # 反转滑动方向

        # 执行滑动操作
        start = area.center  # 滑动起点(屏幕中心)
        end = start + Point(0, 300 * dy)  # 滑动终点
        self.ctx.controller.drag_to(start=start, end=end)

        return self.round_retry(
            status="找不到 %s" % self.mission_type.mission_type_name, wait=1
        )

    def handle_go_button(self, screen, target_point: Point) -> OperationRoundResult:
        """
        处理前往按钮点击逻辑

        参数:
            screen: 当前屏幕截图
            target_point: 目标副本的点击位置

        返回:
            OperationRoundResult - 操作结果对象
        """
        # 获取前往按钮区域
        area = self.ctx.screen_loader.get_area("快捷手册", "前往列表")
        go_rect = area.rect

        # 裁剪出前往按钮区域的图像部分
        part = cv2_utils.crop_image_only(screen, go_rect)

        # 运行OCR识别前往按钮区域的文本
        ocr_results = self.ctx.ocr.run_ocr(part)

        # 初始化前往按钮点击点变量
        target_go_point: Optional[Point] = None

        # 遍历OCR结果，寻找前往按钮
        for ocr_result, mrl in ocr_results.items():
            # 跳过无效的OCR结果
            if mrl.max is None:
                continue

            # 检查是否是前往按钮文本
            if not str_utils.find_by_lcs(gt("前往"), ocr_result, percent=0.5):
                continue

            # 遍历匹配结果，找到最合适的点击位置
            for mr in mrl:
                go_point = go_rect.left_top + mr.center

                # 确保前往按钮在目标副本下方
                if go_point.y <= target_point.y:
                    continue

                # 选择最靠近目标副本的前往按钮
                if target_go_point is None or go_point.y < target_go_point.y:
                    target_go_point = go_point

        # 如果未找到前往按钮，执行滑动操作
        if target_go_point is None:
            # 前往按钮一定在下方，固定向下滑动
            start = area.center
            end = start + Point(0, -200)
            self.ctx.controller.drag_to(start=start, end=end)

            # 返回重试状态
            return self.round_retry(status="找不到 %s" % "前往", wait=1)

        # 点击前往按钮
        click = self.ctx.controller.click(target_go_point)

        # 返回成功状态
        return self.round_success(wait=1)

    @node_from(from_name="选择副本")
    @operation_node(name="确认")
    def confirm(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(
            screen, "快捷手册", "传送确认", success_wait=5, retry_wait=1
        )


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.start_running()
    target = ctx.compendium_service.get_mission_type_data(
        "训练", "定期清剿", "高塔与巨炮"
    )
    op = CompendiumChooseMissionType(ctx, target)
    op.execute()


if __name__ == "__main__":
    __debug()
