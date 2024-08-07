import time

from typing import Optional, ClassVar

from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.application.charge_plan.charge_plan_config import ChargePlanItem
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class NotoriousHunt(ZOperation):

    STATUS_NO_LEFT_TIMES: ClassVar[str] = '没有剩余次数'

    def __init__(self, ctx: ZContext, plan: ChargePlanItem,
                 ):
        """
        使用快捷手册传送后
        用这个进行挑战
        :param ctx:
        """
        ZOperation.__init__(
            self, ctx,
            node_max_retry_times=5,
            op_name='%s %s' % (
                gt('恶名狩猎'),
                gt(plan.mission_type_name)
            )
        )

        self.plan: ChargePlanItem = plan

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        self.charge_left: Optional[int] = None
        self.charge_need: Optional[int] = None

        self.auto_op: Optional[ConditionalOperator] = None

    @operation_node(name='等待入口加载', is_start_node=False)
    def wait_entry_load(self) -> OperationRoundResult:
        self.node_max_retry_times = 60  # 一开始等待加载要久一点
        screen = self.screenshot()
        return self.round_by_find_area(
            screen, '恶名狩猎', '当期剩余奖励次数',
            success_wait=1, retry_wait=1
        )

    @node_from(from_name='等待入口加载')
    @operation_node(name='识别剩余次数')
    def check_left_times(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('恶名狩猎', '剩余次数')
        part = cv2_utils.crop_image_only(screen, area.rect)

        ocr_result = self.ctx.ocr.run_ocr_single_line(part)
        left_times = str_utils.get_positive_digits(ocr_result, None)

        if left_times is None:
            return self.round_retry('未能识别剩余次数', wait_round_time=1)
        elif left_times == 0:
            self.ctx.notorious_hunt_record.left_times = 0
            return self.round_success(NotoriousHunt.STATUS_NO_LEFT_TIMES)
        else:
            self.ctx.notorious_hunt_record.left_times = left_times
            self.can_run_times = min(left_times, self.plan.plan_times - self.plan.run_times)
            return self.round_success()

    @node_from(from_name='识别剩余次数')
    @operation_node(name='选择副本')
    def choose_mission(self) -> OperationRoundResult:
        self.node_max_retry_times = 5

        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('恶名狩猎', '副本名称列表')
        part = cv2_utils.crop_image_only(screen, area.rect)

        ocr_result_map = self.ctx.ocr.run_ocr(part)
        for ocr_result, mrl in ocr_result_map.items():
            if str_utils.find_by_lcs(gt(self.plan.mission_type_name), ocr_result, percent=0.5):
                to_click = mrl.max.center + area.left_top + Point(0, 100)
                if self.ctx.controller.click(to_click):
                    return self.round_success(wait=2)

        return self.round_retry(f'未能识别{self.plan.mission_type_name}', wait_round_time=1)

    @node_from(from_name='选择副本')
    @operation_node(name='下一步')
    def click_next(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(
            screen, '实战模拟室', '下一步',
            success_wait=1, retry_wait_round=1
        )

    @node_from(from_name='下一步')
    @operation_node(name='出战')
    def click_start(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(
            screen, '实战模拟室', '出战',
            success_wait=1, retry_wait_round=1
        )

    @node_from(from_name='出战')
    @node_from(from_name='重新开始-确认')
    @operation_node(name='加载自动战斗指令')
    def init_auto_battle(self) -> OperationRoundResult:
        return auto_battle_utils.load_auto_op(self, 'auto_battle', self.plan.auto_battle_config)

        self.ctx.yolo.init_context(True)
        self.ctx.battle.init_context(
            allow_ultimate_list=self.auto_op.get('allow_ultimate', None)
        )

        return self.round_success()

    @node_from(from_name='加载自动战斗指令')
    @operation_node(name='等待战斗画面加载')
    def wait_battle_screen(self) -> OperationRoundResult:
        self.node_max_retry_times = 60  # 战斗加载的等待时间较长
        screen = self.screenshot()
        return self.round_by_find_area(screen, '战斗画面', '按钮-普通攻击', retry_wait_round=1)

    @node_from(from_name='等待战斗画面加载')
    @operation_node(name='移动交互')
    def move_and_interact(self) -> OperationRoundResult:
        self.ctx.controller.move_w(press=True, press_time=1.5, release=True)

        time.sleep(1)

        self.ctx.controller.interact(press=True, press_time=0.2, release=True)
        time.sleep(2)

        return self.round_success()

    @node_from(from_name='移动交互')
    @operation_node(name='选择')
    def choose_buff(self) -> OperationRoundResult:
        screen = self.screenshot()

        return self.round_by_find_and_click_area(screen, '恶名狩猎', '选择',
                                                 success_wait=1, retry_wait_round=1)

    @node_from(from_name='选择')
    @operation_node(name='向前移动准备战斗')
    def move_to_battle(self) -> OperationRoundResult:
        self.ctx.controller.move_w(press=True, press_time=3, release=True)
        auto_battle_utils.init_context(self)
        self.auto_op.start_running_async()
        return self.round_success()

    @node_from(from_name='向前移动准备战斗')
    @operation_node(name='自动战斗')
    def auto_battle(self) -> OperationRoundResult:
        if self.ctx.battle.is_battle_end():
            self.auto_op.stop_running()
            return self.round_success()
        now = time.time()
        screen = self.screenshot()

        auto_battle_utils.run_screen_check(self, screen, now)

        return self.round_wait(wait=self.ctx.battle_assistant_config.screenshot_interval)

    @node_from(from_name='自动战斗')
    @operation_node(name='战斗结束')
    def after_battle(self) -> OperationRoundResult:
        self.node_max_retry_times = 5  # 战斗结束恢复重试次数
        # TODO 还没有判断战斗失败
        self.can_run_times -= 1
        self.ctx.notorious_hunt_record.left_times = self.ctx.notorious_hunt_record.left_times - 1
        self.ctx.notorious_hunt_config.add_plan_run_times(self.plan)
        return self.round_success()

    @node_from(from_name='战斗结束')
    @operation_node(name='判断下一次')
    def check_next(self) -> OperationRoundResult:
        screen = self.screenshot()
        if self.can_run_times == 0:
            return self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-完成',
                                                     success_wait=5, retry_wait_round=1)
        else:
            return self.round_by_find_and_click_area(screen, '恶名狩猎', '重新开始',
                                                     success_wait=1, retry_wait_round=1)

    @node_from(from_name='判断下一次')
    @operation_node(name='重新开始-确认')
    def restart_confirm(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '恶名狩猎', '重新开始-确认',
                                                 success_wait=1, retry_wait_round=1)

    def _on_pause(self, e=None):
        ZOperation._on_pause(self, e)
        if self.auto_op is not None:
            self.auto_op.stop_running()

    def _on_resume(self, e=None):
        ZOperation._on_resume(self, e)
        if self.auto_op is not None:
            self.auto_op.start_running_async()

    def _after_operation_done(self, result: OperationResult):
        ZOperation._after_operation_done(self, result)
        if self.auto_op is not None:
            self.auto_op.stop_running()
            self.auto_op.dispose()
            self.auto_op = None


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.start_running()
    op = NotoriousHunt(ctx, ChargePlanItem(
        category_name='恶名狩猎',
        mission_type_name='初生死路屠夫'
    ))
    op.can_run_times = 1
    op.execute()


if __name__ == '__main__':
    __debug()
