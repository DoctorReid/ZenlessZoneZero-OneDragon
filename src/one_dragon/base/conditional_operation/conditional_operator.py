import time
from concurrent.futures import ThreadPoolExecutor

from typing import Optional, List, Callable

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_template import OperationTemplate
from one_dragon.base.conditional_operation.scene_handler import SceneHandler, construct_scene_handler
from one_dragon.base.conditional_operation.scene_handler_template import SceneHandlerTemplate
from one_dragon.base.conditional_operation.state_recorder import StateRecorder
from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.base.operation.context_event_bus import ContextEventBus, ContextEventItem
from one_dragon.utils.log_utils import log

_od_conditional_op_executor = ThreadPoolExecutor(thread_name_prefix='od_conditional_op', max_workers=8)


class ConditionalOperator(YamlConfig):

    def __init__(self, module_name: str, sub_dir: Optional[str] = None, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name=module_name,
            sub_dir=[sub_dir],
            instance_idx=instance_idx,
            sample=True
        )

        self.name: str = self.get('name', '')  # 名称
        self._inited: bool = False  # 是否已经完成初始化

        self.event_bus: Optional[ContextEventBus] = None
        self.event_to_scene_handler: dict[str, SceneHandler] = {}  # 需要状态触发的场景处理
        self.normal_scene_handler: Optional[SceneHandler] = None  # 不需要状态触发的场景处理
        self.running: bool = False  # 是否正在运行

    def init(
            self,
            event_bus: ContextEventBus,
            state_recorders: List[StateRecorder],
            op_getter: Callable[[str, List[str]], AtomicOp],
            scene_handler_getter: Callable[[str], SceneHandlerTemplate],
            operation_template_getter: Callable[[str], OperationTemplate],
    ) -> None:
        """
        初始化 在需要执行之前再使用
        """
        self._inited = False

        self.dispose()  # 先把旧的清除掉
        self.event_bus = event_bus
        self.event_to_scene_handler: dict[str, SceneHandler] = {}
        self.normal_scene_handler = None

        scenes = self.get('scenes', [])

        usage_states = []  # 已经监听的状态变更

        for scene_data in scenes:
            handler = construct_scene_handler(scene_data, state_recorders,
                                              op_getter, scene_handler_getter, operation_template_getter)
            states = scene_data.get('triggers', [])
            if len(states) > 0:
                for state in states:
                    if state in usage_states:
                        raise ValueError('状态监听 %s 出现在多个场景中' % state)
                    self.event_to_scene_handler[state] = handler
            elif self.normal_scene_handler is not None:
                raise ValueError('存在多个无状态监听的场景')
            else:
                self.normal_scene_handler = handler

        self._inited = True

    def dispose(self) -> None:
        """
        销毁 要对子模块进行完全销毁
        :return:
        """
        self.stop_running()  # 在这里强制停止运行
        if self.event_to_scene_handler is not None:
            for _, handler in self.event_to_scene_handler.items():
                handler.dispose()
        if self.normal_scene_handler is not None:
            self.normal_scene_handler.dispose()

    def start_running_async(self) -> bool:
        """
        异步开始运行
        :return:
        """
        if not self._inited:
            log.error('自动指令 [ %s ] 未完成初始化 无法运行', self.name)
            return False
        if self.running:
            return False
        self.running = True
        _od_conditional_op_executor.submit(self._execute)
        return True

    def _execute(self) -> None:
        """
        执行具体指令
        :return:
        """
        if self.event_to_scene_handler is not None and self.event_bus is not None:
            for state_event, handler in self.event_to_scene_handler.items():
                self.event_bus.listen_event(state_event, self._on_event)

        if self.normal_scene_handler is not None:
            while self.running:
                self.normal_scene_handler.execute(time.time())

    def _on_event(self, event: ContextEventItem):
        event_id = event.event_id
        if event_id not in self.event_to_scene_handler:
            return

        handler = self.event_to_scene_handler[event_id]

        # 中断当前在执行的指令
        if self.normal_scene_handler is not None:
            self.normal_scene_handler.stop_running()

        for _, another_handler in self.event_to_scene_handler.items():
            if another_handler != handler:
                another_handler.stop_running()

        self.running = True
        handler.execute(event.data)
        self.running = False

    def stop_running(self) -> None:
        """
        停止执行
        :return:
        """
        self.running = False
        if self.event_to_scene_handler is not None:
            for _, handler in self.event_to_scene_handler.items():
                handler.stop_running()
        if self.normal_scene_handler is not None:
            self.normal_scene_handler.stop_running()

        if self.event_bus is not None:
            self.event_bus.unlisten_all_event(self)
