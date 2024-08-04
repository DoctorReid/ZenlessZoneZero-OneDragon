from functools import wraps
from typing import Optional, Callable

from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.base.operation.operation_base import OperationBase


class OperationNode:

    def __init__(self, cn: str,
                 func: Optional[Callable[[], OperationRoundResult]] = None,
                 op_method: Optional[Callable[[OperationBase], OperationRoundResult]] = None,
                 op: Optional[OperationBase] = None,
                 retry_on_op_fail: bool = False,
                 wait_after_op: Optional[float] = None,
                 timeout_seconds: Optional[float] = None,
                 is_start_node: bool = False
                 ):
        """
        带状态指令的节点
        :param cn: 节点名称
        :param func: 该节点用于处理指令的函数 与op只传一个 优先使用func
        :param op: 该节点用于操作的指令 与func只传一个 优先使用func
        :param retry_on_op_fail: op指令失败时是否进入重试
        :param wait_after_op: op指令后的等待时间
        :param timeout_seconds: 该节点的超时秒数
        """

        self.cn: str = cn
        """节点名称"""

        self.func: Callable[[], OperationRoundResult] = func
        """节点处理函数"""

        self.op_method: Optional[Callable[[OperationBase], OperationRoundResult]] = op_method
        """节点处理函数 这个是类方法 需要自己传入self"""

        self.op: Optional[OperationBase] = op
        """节点操作指令"""

        self.retry_on_op_fail: bool = retry_on_op_fail
        """op指令失败时是否进入重试"""

        self.wait_after_op: Optional[float] = wait_after_op
        """op指令后的等待时间"""

        self.timeout_seconds: Optional[float] = timeout_seconds
        """该节点的超时秒数"""

        self.is_start_node: bool = is_start_node
        """是否开始节点"""


def operation_node(
        name: str,
        retry_on_op_fail: bool = False,
        wait_after_op: Optional[float] = None,
        timeout_seconds: Optional[float] = None,
        is_start_node: bool = False,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.__annotations__['operation_node_annotation'] = OperationNode(
            cn=name,
            op_method=func,
            retry_on_op_fail=retry_on_op_fail,
            wait_after_op=wait_after_op,
            timeout_seconds=timeout_seconds,
            is_start_node=is_start_node)
        return wrapper
    return decorator
