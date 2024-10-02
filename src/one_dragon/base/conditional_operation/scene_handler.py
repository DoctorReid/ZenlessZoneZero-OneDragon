from typing import List, Optional,Tuple

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.state_handler import StateHandler


class SceneHandler:

    def __init__(self, interval_seconds: float, state_handlers: List[StateHandler], priority: Optional[int] = None):
        self.interval_seconds: float = interval_seconds
        self.state_handlers: List[StateHandler] = state_handlers
        self.priority: Optional[int] = priority  # 优先级 只能被高等级的打断；为None时可以被随意打断

    def get_operations(self, trigger_time: float) -> Tuple[Optional[List[AtomicOp]],str]:
        """
        获取[处理器handers]内符合条件的[操作集operations]
        :param trigger_time: 触发时间
        :return:
        """
        for sh in self.state_handlers:
            ops,expr = sh.get_operations(trigger_time)
            if ops is not None:
                return ops,expr
        return None,""

    def get_usage_states(self) -> set[str]:
        """
        获取使用的状态
        :return:
        """
        states: set[str] = set()
        for sh in self.state_handlers:
            states = states.union(sh.get_usage_states())
        return states

    def dispose(self) -> None:
        """
        销毁
        :return:
        """
        if self.state_handlers is not None:
            for handler in self.state_handlers:
                handler.dispose()
