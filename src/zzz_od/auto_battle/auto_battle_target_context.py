from typing import List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, Future
import threading
import copy
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Dict, Optional, Callable, Any

from cv2.typing import MatLike
from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.conditional_operation.state_recorder import StateRecord
from one_dragon.utils.log_utils import log
from zzz_od.auto_battle.target_state.target_state_checker import TargetStateChecker
from zzz_od.context.zzz_context import ZContext

# 模块私有的独立线程池，用于并行处理状态检测任务
_target_context_executor = ThreadPoolExecutor(thread_name_prefix='od_target_context', max_workers=8)


class AutoBattleTargetContext:
    """
    目标状态处理上下文。
    负责管理和调度所有与战斗目标（如敌人）相关的状态检测任务。
    它拥有多重计时器，以不同的频率检测不同类型的状态，并将结果批量更新到操作算子中。
    """

    def __init__(self, ctx: ZContext):
        """
        构造函数。
        Args:
            ctx (ZContext): 全局上下文对象，提供诸如截图、日志等基础服务。
        """
        self.ctx: ZContext = ctx
        self.auto_op: Optional[ConditionalOperator] = None
        self.checker: TargetStateChecker = TargetStateChecker(ctx)

        self._check_lock = threading.Lock()

        # 为不同类型的检测任务设置独立的计时器
        self._stagger_check_interval: float = 0.2
        self._stagger_last_check_time: float = 0

        self._abnormal_check_interval: float = 1.0
        self._abnormal_last_check_time: float = 0

        self._lock_check_interval_locked: float = 1.0
        self._lock_check_interval_unlocked: float = 0.1
        self._current_lock_check_interval: float = self._lock_check_interval_unlocked
        self._lock_last_check_time: float = 0

    def init_battle_target_context(self,
                                 auto_op: ConditionalOperator,
                                 check_stagger_interval: float = 0.2,
                                 check_abnormal_interval: float = 1.0,
                                 check_lock_interval_locked: float = 1.0,
                                 check_lock_interval_unlocked: float = 0.1,
                                 **kwargs):
        """
        初始化上下文
        Args:
            auto_op (ConditionalOperator): 操作算子实例，用于后续的状态更新。
            check_stagger_interval (float): 失衡检测间隔
            check_abnormal_interval (float): 异常检测间隔
            check_lock_interval_locked (float): 锁定后的检测间隔
            check_lock_interval_unlocked (float): 未锁定时的检测间隔
        """
        self.auto_op = auto_op
        self._stagger_check_interval = check_stagger_interval
        self._abnormal_check_interval = check_abnormal_interval
        self._lock_check_interval_locked = check_lock_interval_locked
        self._lock_check_interval_unlocked = check_lock_interval_unlocked
        self._current_lock_check_interval = self._lock_check_interval_unlocked
        log.info("目标上下文初始化完成，使用多重计时器 (支持动态间隔)")

    def run_all_checks(self, screen: MatLike, screenshot_time: float):
        """
        根据各自的计时器，检测所有到期的目标状态。
        锁定检测(CV)速度快，将同步执行。
        OCR任务(失衡、异常)速度慢，将异步执行。
        这是模块的主入口，由外部的统一战斗循环在每一帧调用。
        Args:
            screen (MatLike): 屏幕截图.
            screenshot_time (float): 截图时间戳.
        """
        if self.auto_op is None or not self.auto_op.is_running:
            return

        if not self._check_lock.acquire(blocking=False):
            return

        try:
            now = screenshot_time
            records_to_update: List[StateRecord] = []
            futures: List[Future] = []

            # 1. 同步执行快速的CV任务
            if now - self._lock_last_check_time >= self._current_lock_check_interval:
                self._lock_last_check_time = now
                lock_results = self.checker.check_lock_on(screen)
                # 核心逻辑：根据结果动态调整下一次的检测间隔
                for state_name, _ in lock_results:
                    if state_name == '目标-近距离锁定':
                        self._current_lock_check_interval = self._lock_check_interval_locked
                        break
                    elif state_name == '目标-未锁定':
                        self._current_lock_check_interval = self._lock_check_interval_unlocked
                        break
                self._add_records_from_results(records_to_update, lock_results, screenshot_time)

            # 2. 异步提交耗时的OCR任务
            if now - self._stagger_last_check_time >= self._stagger_check_interval:
                self._stagger_last_check_time = now
                futures.append(_target_context_executor.submit(self.checker.check_enemy_type_and_stagger, screen))

            if now - self._abnormal_last_check_time >= self._abnormal_check_interval:
                self._abnormal_last_check_time = now
                futures.append(_target_context_executor.submit(self.checker.check_abnormal_statuses, screen))

            # 3. 处理异步任务结果
            for future in futures:
                try:
                    results = future.result(timeout=3)
                    self._add_records_from_results(records_to_update, results, screenshot_time)
                except Exception:
                    log.error(f"异步检测目标状态失败", exc_info=True)

            # 4. 批量提交状态更新
            if records_to_update:
                self.auto_op.batch_update_states(records_to_update)

        finally:
            self._check_lock.release()

    def _add_records_from_results(self, records_list: List[StateRecord],
                                  results: List[Tuple[str, Any]],
                                  screenshot_time: float):
        """
        一个辅助方法，用于将检测结果列表转换为StateRecord并添加到主列表中
        """
        if not results:
            return
        
        for state_name, value in results:
            record_value = value
            if isinstance(value, bool):
                record_value = 1 if value else 0
            records_list.append(StateRecord(state_name, screenshot_time, record_value))
