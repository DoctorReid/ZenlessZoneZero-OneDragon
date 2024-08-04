from functools import wraps

from typing import Optional

from one_dragon.base.operation.operation_node import OperationNode


class OperationEdge:

    def __init__(self, node_from: OperationNode, node_to: OperationNode,
                 success: bool = True, status: Optional[str] = None, ignore_status: bool = True):
        """
        带状态指令的边
        :param node_from: 上一个指令
        :param node_to: 下一个指令
        :param success: 是否成功才进入下一个节点
        :param status: 上一个节点的结束状态 符合时才进入下一个节点
        :param ignore_status: 是否忽略状态进行下一个节点 不会忽略success
        """

        self.node_from: OperationNode = node_from
        """上一个节点"""

        self.node_to: OperationNode = node_to
        """下一个节点"""

        self.success: bool = success
        """是否成功才执行下一个节点"""

        self.status: Optional[str] = status
        """
        执行下一个节点的条件状态 
        一定要完全一样才会执行 包括None
        """

        self.ignore_status: bool = False if status is not None else ignore_status
        """
        是否忽略状态进行下一个节点
        一个节点应该最多只有一条边忽略返回状态
        忽略返回状态只有在所有需要匹配的状态都匹配不到时才会用做兜底
        """


class OperationEdgeDesc:

    def __init__(self, node_from_name: str, node_to_name: str,
                 success: bool = True, status: Optional[str] = None, ignore_status: bool = True):
        """
        边描述
        """
        self.node_from_name: str = node_from_name
        self.node_to_name: str = node_to_name
        self.success: bool = success
        self.status: Optional[str] = status
        self.ignore_status: bool = ignore_status


def node_from(
        from_name: str,
        success: bool = True,
        status: Optional[str] = None,
        ignore_status: bool = True,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        if 'operation_edge_annotation' not in wrapper.__annotations__:
            wrapper.__annotations__['operation_edge_annotation'] = []
        else:
            pass

        wrapper.__annotations__['operation_edge_annotation'].append(
            OperationEdgeDesc(
            node_from_name=from_name,
            node_to_name=None,
            success=success,
            status=status,
            ignore_status=ignore_status,
        ))
        return wrapper
    return decorator
