import time

from typing import Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.hollow_zero.hollow_zero_event import HollowZeroSpecialEvent
from zzz_od.operation.zzz_operation import ZOperation


class HollowBattle(ZOperation):

    def __init__(self, ctx: ZContext, is_critical_stage: bool = False):
        """
        确定出现事件后调用
        :param ctx:
        """
        event_name = HollowZeroSpecialEvent.IN_BATTLE.value.event_name
        ZOperation.__init__(
            self, ctx,
            node_max_retry_times=5,
            op_name=gt(event_name)
        )

        self.is_critical_stage: bool = is_critical_stage  # 是否关键进展
        self.auto_op: Optional[AutoBattleOperator] = None

    def handle_init(self):
        self.last_no_distince_times: int = 0

    @operation_node(name='加载自动战斗指令', is_start_node=True)
    def load_auto_op(self) -> OperationRoundResult:
        return auto_battle_utils.load_auto_op(
            self, 'auto_battle',
            self.ctx.battle_assistant_config.auto_battle_config
        )

    @node_from(from_name='加载自动战斗指令')
    @operation_node(name='等待战斗画面加载')
    def wait_battle_screen(self) -> OperationRoundResult:
        self.node_max_retry_times = 60  # 战斗加载的等待时间较长
        screen = self.screenshot()
        result = self.round_by_find_area(screen, '战斗画面', '按钮-普通攻击', retry_wait_round=1)
        return result

    @node_from(from_name='等待战斗画面加载')
    @operation_node(name='初始化上下文')
    def init_context(self) -> OperationRoundResult:
        auto_battle_utils.init_context(self)

        self.ctx.hollow.init_context(
            check_end_interval=self.auto_op.get('check_end_interval', 5),
        )
        return self.round_success()

    @node_from(from_name='初始化上下文')
    @operation_node(name='副本特殊移动')
    def special_move(self):
        # TODO 双重危机里也有不规则的移动
        if (self.ctx.hollow.level_info.is_mission_type('旧都列车', 2)
            and self.ctx.hollow.level_info.level == 2):
            self.ctx.controller.move_w(press=True, press_time=1.5)

        else:
            self.ctx.controller.move_w(press=True, press_time=1.5)

        return self.round_success()

    @node_from(from_name='副本特殊移动')
    @operation_node(name='向前移动准备战斗')
    def move_to_battle(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('战斗画面', '距离显示区域')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part)

        distance: Optional[float] = None
        pos: Optional[Point] = None
        for ocr_result, mrl in ocr_result_map.items():
            if not ocr_result.endswith('m'):
                continue
            pre_str = ocr_result[:-1]
            distance = str_utils.get_positive_float(pre_str, None)
            if distance is None:
                continue
            pos = mrl.max.center + area.left_top

        if distance is None:
            self.last_no_distince_times += 1
            if self.last_no_distince_times >= 10:
                self.auto_op.start_running_async()
                return self.round_success()
            else:
                return self.round_wait(wait=0.02)

        self.last_no_distince_times = 0

        if pos.x < 900:
            self.ctx.controller.turn_by_distance(-50)
            return self.round_wait(wait=0.5)
        elif pos.x > 1100:
            self.ctx.controller.turn_by_distance(+50)
            return self.round_wait(wait=0.5)
        else:
            self.ctx.controller.move_w(press=1, press_time=0.5, release=True)
            return self.round_wait(wait=0.5)

    @node_from(from_name='向前移动准备战斗')
    @operation_node(name='自动战斗')
    def auto_battle(self) -> OperationRoundResult:
        # TODO 战斗中途可能需要移动
        if self.ctx.hollow.last_check_end_result is not None:
            self.auto_op.stop_running()
            return self.round_success(status=self.ctx.hollow.last_check_end_result)
        now = time.time()
        screen = self.screenshot()

        auto_battle_utils.run_screen_check(self, screen, now)
        self.ctx.hollow.check_screen(screen, now,
                                     check_battle_end=True)

        return self.round_wait(wait=self.ctx.battle_assistant_config.screenshot_interval)

    @node_from(from_name='自动战斗', status='挑战结果')
    @operation_node(name='战斗结束')
    def after_battle(self) -> OperationRoundResult:
        self.node_max_retry_times = 5  # 战斗结束恢复重试次数
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('零号空洞-事件', '战斗结果-确定')
        return self.round_by_ocr_and_click(screen, '确定', area=area,
                                           success_wait=1, retry_wait=1)

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
