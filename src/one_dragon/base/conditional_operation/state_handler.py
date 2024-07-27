from typing import List, Callable, Set

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_template import OperationTemplate
from one_dragon.base.conditional_operation.state_cal_tree import construct_state_cal_tree, StateCalNode
from one_dragon.base.conditional_operation.state_recorder import StateRecorder


class StateHandler:

    def __init__(self,
                 state_cal_tree: StateCalNode,
                 operations: List[AtomicOp]
                 ):
        """
        一个状态处理器 包含状态判断 + 对应指令
        :param state_cal_tree: 状态判断树
        :param operations: 执行指令
        """
        self.state_cal_tree: StateCalNode = state_cal_tree
        self.operations: List[AtomicOp] = operations
        self.running: bool = False  # 当前是否在执行指令

    def check_and_run(self, now: float) -> bool:
        """
        判断是否符合条件 符合的话就执行指令
        :param now: 当前判断时间
        :return: 是否运行
        """
        if self.state_cal_tree.in_time_range(now):
            self.running = True
            self._execute()
            return True
        else:
            return False

    def _execute(self) -> None:
        """
        执行具体的指令
        :return:
        """
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


def construct_state_handler(
        state_data: dict,
        state_recorders: List[StateRecorder],
        op_getter: Callable[[str, List[str]], AtomicOp],
        operation_template_getter: Callable[[str], OperationTemplate],
) -> StateHandler:
    """
    构造一个场景处理器
    包含状态判断 + 对应指令
    :param state_data: 场景配置数据
    :param state_recorders: 状态记录器
    :param op_getter: 指令获取器
    :param operation_template_getter: 指令模板获取器
    :return:
    """
    state_cal_tree = construct_state_cal_tree(state_data.get("states", ''), state_recorders)

    ops = _get_ops_from_data(state_data.get('operations', []),
                             op_getter, operation_template_getter,
                             set())

    return StateHandler(state_cal_tree, ops)


def construct_op_by_template(
        template_name: str,
        op_getter: Callable[[str, List[str]], AtomicOp],
        operation_template_getter: Callable[[str], OperationTemplate],
        usage_templates: Set[str]
) -> List[AtomicOp]:
    if template_name in usage_templates:
        raise ValueError('循环引入指令模板 ' + template_name)
    if template_name is None or len(template_name) == 0:
        raise ValueError('指令模板名称为空 handler_template')
    template: OperationTemplate = operation_template_getter(template_name)
    if template is None:
        raise ValueError('找不到指令模板 ' + template_name)

    usage_templates.add(template_name)
    ops = _get_ops_from_data(template.get('operations', []),
                             op_getter, operation_template_getter,
                             usage_templates)

    usage_templates.remove(template_name)

    return ops


def _get_ops_from_data(
        operation_data_list: List[dict],
        op_getter: Callable[[str, List[str]], AtomicOp],
        operation_template_getter: Callable[[str], OperationTemplate],
        usage_templates: Set[str]
):
    ops = []
    for operation_data_item in operation_data_list:
        if 'operation_template' in operation_data_item:
            template_ops = construct_op_by_template(
                operation_data_item['operation_template'],
                op_getter, operation_template_getter,
                usage_templates
            )
            for op in template_ops:
                ops.append(op)
        else:
            op_name = operation_data_item.get('op_name', '')
            op_data = operation_data_item.get('data', [])
            op = op_getter(op_name, op_data)
            ops.append(op)
    return ops
