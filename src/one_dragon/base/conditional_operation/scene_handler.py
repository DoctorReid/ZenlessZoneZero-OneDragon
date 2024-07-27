from typing import List, Callable, Set

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_template import OperationTemplate
from one_dragon.base.conditional_operation.scene_handler_template import SceneHandlerTemplate
from one_dragon.base.conditional_operation.state_handler import StateHandler, construct_state_handler
from one_dragon.base.conditional_operation.state_recorder import StateRecorder


class SceneHandler:

    def __init__(self, interval_seconds: float, state_handlers: List[StateHandler]):
        self.interval_seconds: float = interval_seconds
        self.state_handlers: List[StateHandler] = state_handlers
        self.last_trigger_time: float = 0

    def execute(self, now: float) -> None:
        """
        按优先级判断状态 找到需要执行的执行并执行
        :param now:
        :return:
        """
        if now - self.last_trigger_time <= self.interval_seconds:
            return
        self.last_trigger_time = now
        for sh in self.state_handlers:
            if sh.check_and_run(now):
                return

    def stop_running(self) -> None:
        """
        停止运行
        :return:
        """
        for sh in self.state_handlers:
            sh.stop_running()

    def dispose(self) -> None:
        """
        销毁
        :return:
        """
        if self.state_handlers is not None:
            for handler in self.state_handlers:
                handler.dispose()


def construct_scene_handler(
        scene_data: dict,
        state_recorders: List[StateRecorder],
        op_getter: Callable[[str, List[str]], AtomicOp],
        scene_handler_getter: Callable[[str], SceneHandlerTemplate],
        operation_template_getter: Callable[[str], OperationTemplate],
):
    interval_seconds = scene_data.get('interval', 0.5)

    state_handlers = _get_state_handlers(
        scene_data.get('handlers', []),
        state_recorders, op_getter, scene_handler_getter, operation_template_getter,
        set()
    )

    return SceneHandler(interval_seconds, state_handlers)


def construct_handler_by_template(
        template_name: str,
        state_recorders: List[StateRecorder],
        op_getter: Callable[[str, List[str]], AtomicOp],
        scene_handler_getter: Callable[[str], SceneHandlerTemplate],
        operation_template_getter: Callable[[str], OperationTemplate],
        usage_templates: Set[str]
) -> List[StateHandler]:
    """
    根据模板加载
    :return:
    """
    if template_name in usage_templates:
        raise ValueError('循环引入场景处理器模板 ' + template_name)
    if template_name is None or len(template_name) == 0:
        raise ValueError('场景处理器模板名称为空 handler_template')
    template: SceneHandlerTemplate = scene_handler_getter(template_name)
    if template is None:
        raise ValueError('找不到场景处理器模板 ' + template_name)

    usage_templates.add(template_name)
    state_handlers = _get_state_handlers(
        template.get('handlers', []),
        state_recorders, op_getter, scene_handler_getter, operation_template_getter,
        usage_templates
    )
    usage_templates.remove(template_name)

    return state_handlers


def _get_state_handlers(
        handler_data_list: List[dict],
        state_recorders: List[StateRecorder],
        op_getter: Callable[[str, List[str]], AtomicOp],
        scene_handler_getter: Callable[[str], SceneHandlerTemplate],
        operation_template_getter: Callable[[str], OperationTemplate],
        usage_templates: Set[str]
) -> List[StateHandler]:
    state_handlers = []

    for handler_data_item in handler_data_list:
        if 'handler_template' in handler_data_item:
            template_state_handlers = construct_handler_by_template(
                handler_data_item.get('handler_template', ''),
                state_recorders, op_getter, scene_handler_getter, operation_template_getter,
                usage_templates)
            for i in template_state_handlers:
                state_handlers.append(i)
        else:
            state_handlers.append(construct_state_handler(handler_data_item, state_recorders,
                                                          op_getter, operation_template_getter))

    return state_handlers
