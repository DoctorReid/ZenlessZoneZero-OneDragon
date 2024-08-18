import time

from cv2.typing import MatLike
from typing import Optional, ClassVar

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.context.zzz_context import ZContext
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroSpecialEvent
from zzz_od.operation.zzz_operation import ZOperation


class HollowBattle(ZOperation):

    STATUS_NEED_SPECIAL_MOVE: ClassVar[str] = '需要移动'
    STATUS_NO_NEED_SPECIAL_MOVE: ClassVar[str] = '不需要移动'

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
        self.distance_pos: Optional[Rect] = None  # 显示距离的区域

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
        return self.round_success()

    @node_from(from_name='初始化上下文')
    @operation_node(name='识别特殊移动')
    def check_special_move(self):
        screen = self.screenshot()
        self._check_distance(screen)

        if self.ctx.battle.with_distance_times >= 10:
            return self.round_success(HollowBattle.STATUS_NEED_SPECIAL_MOVE)
        if self.ctx.battle.without_distance_times >= 10:
            self.auto_op.start_running_async()
            return self.round_success(HollowBattle.STATUS_NO_NEED_SPECIAL_MOVE)

        return self.round_wait()

    @node_from(from_name='识别特殊移动', status=STATUS_NEED_SPECIAL_MOVE)
    @operation_node(name='副本特殊移动')
    def special_move(self):
        if (self.ctx.hollow.level_info.is_mission_type('旧都列车', 2)
            and self.ctx.hollow.level_info.level == 2):
            self.ctx.controller.move_w(press=True, press_time=1.5)
        else:
            self.ctx.controller.move_w(press=True, press_time=1.5)

        return self.round_success()

    @node_from(from_name='副本特殊移动')
    @node_from(from_name='自动战斗', status=STATUS_NEED_SPECIAL_MOVE)
    @operation_node(name='向前移动准备战斗')
    def move_to_battle(self) -> OperationRoundResult:
        screen = self.screenshot()
        self._check_distance(screen)

        if self.distance_pos is None:
            if self.ctx.battle.without_distance_times >= 10:
                self.auto_op.start_running_async()
                return self.round_success()
            else:
                return self.round_wait(wait=0.02)

        pos = self.distance_pos.center
        if pos.x < 900:
            self.ctx.controller.turn_by_distance(-50)
            return self.round_wait(wait=0.5)
        elif pos.x > 1100:
            self.ctx.controller.turn_by_distance(+50)
            return self.round_wait(wait=0.5)
        else:
            press_time = self.ctx.battle.last_check_distance / 7.2  # 朱鸢测出来的速度
            self.ctx.controller.move_w(press=True, press_time=press_time, release=True)
            return self.round_wait(wait=0.5)

    @node_from(from_name='识别特殊移动', status=STATUS_NO_NEED_SPECIAL_MOVE)
    @node_from(from_name='向前移动准备战斗')
    @operation_node(name='自动战斗')
    def auto_battle(self) -> OperationRoundResult:
        if self.ctx.battle.last_check_end_result is not None:
            auto_battle_utils.stop_running(self)
            return self.round_success(status=self.ctx.battle.last_check_end_result)

        if self.ctx.battle.with_distance_times >= 5:
            auto_battle_utils.stop_running(self)
            return self.round_success(status=HollowBattle.STATUS_NEED_SPECIAL_MOVE)

        now = time.time()
        screen = self.screenshot()

        auto_battle_utils.run_screen_check(self, screen, now,
                                           check_battle_end_normal_result=True,
                                           check_battle_end_hollow_result=True,
                                           check_battle_end_hollow_bag=True,
                                           check_distance=True)

        return self.round_wait(wait=self.ctx.battle_assistant_config.screenshot_interval)

    @node_from(from_name='自动战斗', status='零号空洞-挑战结果')
    @operation_node(name='战斗结果-确定')
    def after_battle(self) -> OperationRoundResult:
        self.node_max_retry_times = 5  # 战斗结束恢复重试次数
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('零号空洞-事件', '战斗结果-确定')
        return self.round_by_ocr_and_click(screen, '确定', area=area,
                                           success_wait=1, retry_wait=1)

    @node_from(from_name='战斗结果-确定')
    @operation_node(name='更新楼层信息')
    def update_level_info(self) -> OperationRoundResult:
        if self.is_critical_stage:
            self.ctx.hollow.update_to_next_level()
        return self.round_success()

    @node_from(from_name='自动战斗', status='普通战斗-撤退')
    @operation_node(name='战斗撤退')
    def battle_fail(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-撤退',
                                                 success_wait=1, retry_wait=1)

    def _check_distance(self, screen: MatLike) -> None:
        mr = self.ctx.battle.check_battle_distance(screen)

        if mr is None:
            self.distance_pos = None
        else:
            self.distance_pos = mr.rect

    def _on_pause(self, e=None):
        ZOperation._on_pause(self, e)
        auto_battle_utils.stop_running(self)

    def _on_resume(self, e=None):
        ZOperation._on_resume(self, e)
        auto_battle_utils.resume_running(self)

    def _after_operation_done(self, result: OperationResult):
        ZOperation._after_operation_done(self, result)
        auto_battle_utils.stop_running(self)
        if self.auto_op is not None:
            self.auto_op.dispose()
            self.auto_op = None
