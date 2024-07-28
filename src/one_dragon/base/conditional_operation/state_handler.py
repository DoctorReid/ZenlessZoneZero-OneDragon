from typing import List, Optional

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.state_cal_tree import StateCalNode
from one_dragon.utils.log_utils import log


class StateHandler:

    def __init__(self,
                 expr: str,
                 state_cal_tree: StateCalNode,
                 sub_states: Optional[List] = None,
                 operations: Optional[List[AtomicOp]] = None
                 ):
        """
        一个状态处理器 包含状态判断 + 对应指令
        :param state_cal_tree: 状态判断树
        :param operations: 执行指令
        """
        self.expr: str = expr
        self.state_cal_tree: StateCalNode = state_cal_tree
        self.sub_states: List[StateHandler] = sub_states
        self.operations: List[AtomicOp] = operations
        self.running: bool = False  # 当前是否在执行指令

    def check_and_run(self, now: float) -> bool:
        """
        判断是否符合条件 符合的话就执行指令
        :param now: 当前判断时间
        :return: 是否运行
        """
        if self.state_cal_tree.in_time_range(now):
            if self.sub_states is not None and len(self.sub_states) > 0:
                for sub_state in self.sub_states:
                    if sub_state.check_and_run(now):
                        return True
            else:
                log.debug('触发条件 %s', self.expr)
                self._execute()
                return True
        else:
            return False

    def _execute(self) -> None:
        """
        执行具体的指令
        :return:
        """
        self.running = True
        for op in self.operations:
            if not self.running:
                break

            op.execute()
        self.running = False

    def stop_running(self) -> None:
        """
        停止运行
        :return:
        """
        self.running = False

    def dispose(self) -> None:
        """
        销毁
        :return:
        """
        self.stop_running()
        if self.state_cal_tree is not None:
            self.state_cal_tree.dispose()
        if self.operations is not None:
            for op in self.operations:
                op.dispose()
        if self.sub_states is not None:
            for sub_state in self.sub_states:
                sub_state.dispose()
