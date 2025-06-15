import threading
import copy
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Dict, Optional, Callable, Any

from cv2.typing import MatLike
from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.conditional_operation.state_recorder import StateRecord
from one_dragon.utils.log_utils import log
from one_dragon.utils.cal_utils import random_in_range
from zzz_od.auto_battle.target_state.target_state_checker import (
    check_enemy_type,
    check_stagger_value,
    check_abnormal_status,
    check_lock_distance,
    BUILTIN_TARGET_STATE_DEFS
)
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.target_state import TargetStateDef, TargetStateCheckWay, EnemyTypeValue, LockDistanceValue

# 模块私有的独立线程池，用于并行处理状态检测任务
_target_context_executor = ThreadPoolExecutor(thread_name_prefix='od_target_context', max_workers=8)

# 检测方式与具体检测函数的映射字典，用于解耦调度与实现
_target_state_check_method: Dict[TargetStateCheckWay, Callable] = {
    TargetStateCheckWay.ENEMY_TYPE: check_enemy_type,
    TargetStateCheckWay.STAGGER: check_stagger_value,
    TargetStateCheckWay.ABNORMAL: check_abnormal_status,
    TargetStateCheckWay.LOCK_DISTANCE: check_lock_distance,
}



class AutoBattleTargetContext:
    """
    目标状态处理上下文 (与 AgentContext 模式完全一致)。
    负责管理和调度所有与战斗目标（如敌人）相关的状态检测任务。
    它由外部的统一战斗循环驱动，并将检测到的状态批量更新到操作算子中。
    """

    def __init__(self, ctx: ZContext):
        """
        构造函数。
        Args:
            ctx (ZContext): 全局上下文对象，提供诸如截图、日志等基础服务。
        """
        self.ctx: ZContext = ctx
        self.auto_op: Optional[ConditionalOperator] = None
        self.target_defs: List[TargetStateDef] = []

        self._check_lock = threading.Lock()
        self._check_interval: float = 0.1  # 默认检测间隔
        self._last_check_time: float = 0

    def init_battle_target_context(self,
                                 auto_op: ConditionalOperator,
                                 check_target_interval: float = 0.1,
                                 **kwargs):
        """
        初始化上下文 (V5 - 统一时间管理)
        Args:
            auto_op (ConditionalOperator): 操作算子实例，用于后续的状态更新。
            check_target_interval (float): 检测间隔
        """
        self.auto_op = auto_op
        self._check_interval = check_target_interval
        # 直接使用内置状态定义
        self.target_defs = copy.deepcopy(BUILTIN_TARGET_STATE_DEFS)
        log.info(f"目标上下文初始化完成，加载 {len(self.target_defs)} 个内置状态定义")

    def check_target_states_in_parallel(self, screen: MatLike, screenshot_time: float):
        """
        并行检测所有到期的目标状态。
        这是模块的主入口，由外部的统一战斗循环在每一帧调用。
        Args:
            screen (MatLike): 屏幕截图.
            screenshot_time (float): 截图时间戳.
        """
        if self.auto_op is None or not self.auto_op.is_running:
            return

        if screenshot_time - self._last_check_time < random_in_range(self._check_interval):
            return

        if not self._check_lock.acquire(blocking=False):
            return

        try:
            self._last_check_time = screenshot_time
            future_map: Dict[Future, TargetStateDef] = {}
            for state_def in self.target_defs:
                if not state_def.enabled:
                    continue

                check_method = _target_state_check_method.get(state_def.check_way)
                if check_method:
                    future = _target_context_executor.submit(
                        check_method,
                        ctx=self.ctx,
                        screen=screen,
                        config_params=state_def.config_params
                    )
                    future_map[future] = state_def

            if not future_map:
                return

            self._process_futures_and_update_states(future_map, screenshot_time)

        finally:
            self._check_lock.release()

    def _process_futures_and_update_states(self, future_map: Dict[Future, TargetStateDef], screenshot_time: float):
        """
        处理已完成的异步检测任务，并将结果批量更新到操作算子。
        Args:
            future_map (Dict[Future, TargetStateDef]): 一个字典，键是Future对象，值是对应的状态定义。
            screenshot_time (float): 截图的时间戳，用于生成状态记录。
        """
        records_to_update: List[StateRecord] = []
        for future, state_def in future_map.items():
            try:
                result = future.result(timeout=5)

                # V12: 按需更新。如果checker返回None，则不更新该状态
                if result is None:
                    continue

                # V3设计：所有状态检测结果直接转换为StateRecord
                # bool值也转为0/1
                value = result
                if isinstance(result, bool):
                    value = 1 if result else 0

                # 更新基础状态
                records_to_update.append(StateRecord(state_def.state_name, screenshot_time, value))

                # 根据基础状态，派生出虚拟状态，用于bool判断 (V8: 采用 '目标-值' 的简洁模式)
                if state_def.check_way == TargetStateCheckWay.ENEMY_TYPE:
                    display_map = EnemyTypeValue.get_display_map()
                    for enum_member, display_name in display_map.items():
                        is_current_type = (value == enum_member.value)
                        records_to_update.append(
                            StateRecord(f'目标-{display_name}', screenshot_time, is_clear=not is_current_type)
                        )
                elif state_def.check_way == TargetStateCheckWay.LOCK_DISTANCE:
                    display_map = LockDistanceValue.get_display_map()
                    for enum_member, display_name in display_map.items():
                        is_current_dist = (value == enum_member.value)
                        records_to_update.append(
                            StateRecord(f'目标-{display_name}', screenshot_time, is_clear=not is_current_dist)
                        )

            except Exception:
                log.error(f"检测目标状态失败: {state_def.state_name}", exc_info=True)

        if records_to_update:
            self.auto_op.batch_update_states(records_to_update)
