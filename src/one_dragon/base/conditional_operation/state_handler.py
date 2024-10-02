from typing import List, Optional,Tuple

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
        """ 子状态state """
        self.operations: List[AtomicOp] = operations
        """ 操作集operations """

    def get_operations(self, trigger_time: float) -> Tuple[Optional[List[AtomicOp]], str]:
        """
        根据[场景scene]的触发条件,返回第一个符合的[操作集operations]和对应的[条件集states]
        :param trigger_time:
        :return:
        """
        # 若触发时间在状态时间的范围内,则继续
        if not self.state_cal_tree.in_time_range(trigger_time):
            return None, None

        log.debug('满足条件 %s', self.expr)

        # 如果有子条件,则循环判断子条件
        if self.sub_states:
            for sub_state in self.sub_states:
                ops, expr = sub_state.get_operations(trigger_time)
                if ops is not None:
                    return ops, expr

        # 没有子条件,则返回自身的操作
        return self.operations, self.expr

    def get_usage_states(self) -> set[str]:
        """
        获取使用的状态
        :return:
        """
        states: set[str] = set()
        if self.state_cal_tree is not None:
            states = states.union(self.state_cal_tree.get_usage_states())
        if self.sub_states is not None:
            for sub in self.sub_states:
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
        if self.sub_states is not None:
            for sub_state in self.sub_states:
                sub_state.dispose()
