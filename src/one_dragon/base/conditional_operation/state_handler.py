from typing import List, Optional, Tuple

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.state_cal_tree import StateCalNode
from one_dragon.utils.log_utils import log


class StateHandler:

    def __init__(self,
                 expr: str,
                 state_cal_tree: StateCalNode,
                 sub_handlers: Optional[List] = None,
                 operations: Optional[List[AtomicOp]] = None
                 ):
        """
        一个状态处理器 包含状态判断 + 对应指令
        :param state_cal_tree: 状态判断树
        :param operations: 执行指令
        """
        self.expr: str = expr
        self.state_cal_tree: StateCalNode = state_cal_tree
        self.sub_handlers: List[StateHandler] = sub_handlers
        self.operations: List[AtomicOp] = operations

    def get_operations(self, trigger_time: float) -> Tuple[Optional[List[AtomicOp]], str]:
        """
        根据触发时间 和优先级 获取符合条件的场景下的指令
        :param trigger_time:
        :return:
        """
        if self.state_cal_tree.in_time_range(trigger_time):
            log.debug('满足条件 %s', self.expr)
            if self.sub_handlers is not None and len(self.sub_handlers) > 0:
                for sub_handler in self.sub_handlers:
                    ops, expr = sub_handler.get_operations(trigger_time)
                    if ops is not None:
                        return ops, expr
            else:
                return self.operations, self.expr

        return None, ''

    def get_usage_states(self) -> set[str]:
        """
        获取使用的状态
        :return:
        """
        states: set[str] = set()
        if self.state_cal_tree is not None:
            states = states.union(self.state_cal_tree.get_usage_states())
        if self.sub_handlers is not None:
            for sub in self.sub_handlers:
                states = states.union(sub.get_usage_states())
        return states


    def dispose(self) -> None:
        """
        销毁
        :return:
        """
        if self.state_cal_tree is not None:
            self.state_cal_tree.dispose()
        if self.operations is not None:
            for op in self.operations:
                op.dispose()
        if self.sub_handlers is not None:
            for sub in self.sub_handlers:
                sub.dispose()
