import time
from concurrent.futures import ThreadPoolExecutor, Future

from threading import Lock
from typing import Optional, List, Callable

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_task import OperationTask
from one_dragon.base.conditional_operation.operation_template import OperationTemplate
from one_dragon.base.conditional_operation.scene_handler import SceneHandler
from one_dragon.base.conditional_operation.state_handler_template import StateHandlerTemplate
from one_dragon.base.conditional_operation.state_recorder import StateRecorder
from one_dragon.base.conditional_operation.utils import construct_scene_handler
from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.base.operation.context_event_bus import ContextEventBus, ContextEventItem
from one_dragon.thread.atomic_int import AtomicInt
from one_dragon.utils import thread_utils
from one_dragon.utils.log_utils import log

_od_conditional_op_executor = ThreadPoolExecutor(thread_name_prefix='od_conditional_op', max_workers=4)


class ConditionalOperator(YamlConfig):

    def __init__(self, sub_dir: str, template_name: str,
                 instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name=template_name,
            sub_dir=[sub_dir],
            instance_idx=instance_idx,
            sample=True, copy_from_sample=False
        )

        self._inited: bool = False  # 是否已经完成初始化

        self.event_bus: Optional[ContextEventBus] = None
        self._event_to_scene_handler: dict[str, SceneHandler] = {}  # 需要状态触发的场景处理
        self._event_trigger_time: dict[str, float] = {}  # 触发时间
        self._normal_scene_handler: Optional[SceneHandler] = None  # 不需要状态触发的场景处理
        self._running: bool = False  # 整体是否正在运行
        self.normal_scene_running: bool = False  # 不需要状态触发的场景是否在执行
        self.special_scene_running: bool = False  # 需要状态触发的场景是否在执行

        self._task_lock: Lock = Lock()
        self._running_task: Optional[OperationTask] = None  # 正在运行的任务
        self._running_trigger_cnt: AtomicInt = AtomicInt()

    def init(
            self,
            event_bus: ContextEventBus,
            state_recorders: List[StateRecorder],
            op_getter: Callable[[str, List[str]], AtomicOp],
            scene_handler_getter: Callable[[str], StateHandlerTemplate],
            operation_template_getter: Callable[[str], OperationTemplate],
    ) -> None:
        """
        初始化 在需要执行之前再使用
        """
        self._inited = False

        self.dispose()  # 先把旧的清除掉
        self.event_bus = event_bus
        self._event_to_scene_handler: dict[str, SceneHandler] = {}
        self._normal_scene_handler = None
        self._event_trigger_time = {}

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
                    self._event_to_scene_handler[state] = handler
            elif self._normal_scene_handler is not None:
                raise ValueError('存在多个无状态监听的场景')
            else:
                self._normal_scene_handler = handler

        self._inited = True

    def dispose(self) -> None:
        """
        销毁 要对子模块进行完全销毁
        :return:
        """
        self.stop_running()  # 在这里强制停止运行
        if self._event_to_scene_handler is not None:
            for _, handler in self._event_to_scene_handler.items():
                handler.dispose()
        if self._normal_scene_handler is not None:
            self._normal_scene_handler.dispose()

    def start_running_async(self) -> bool:
        """
        异步开始运行
        :return:
        """
        if not self._inited:
            log.error('自动指令 [ %s ] 未完成初始化 无法运行', self.name)
            return False
        if self._running:
            return False
        self._running = True

        if self._event_to_scene_handler is not None and self.event_bus is not None:
            self.event_bus.unlisten_all_event(self)
            for state_event, handler in self._event_to_scene_handler.items():
                self.event_bus.listen_event(state_event, self._on_event)

        if self._normal_scene_handler is not None:
            future: Future = _od_conditional_op_executor.submit(self._normal_scene_loop)
            future.add_done_callback(thread_utils.handle_future_result)

        return True

    def _normal_scene_loop(self) -> None:
        """
        主循环
        :return:
        """
        while True:
            if self._running_trigger_cnt.get() > 0:
                time.sleep(0.02)
            else:
                trigger_time = time.time()
                to_sleep: Optional[float] = None
                future: Optional[Future] = None

                # 上锁后判断是否新建任务
                with self._task_lock:
                    if not self._running:
                        break
                    last_trigger_time = self._event_trigger_time.get('', 0)
                    past_time = trigger_time - last_trigger_time
                    if past_time < self._normal_scene_handler.interval_seconds:
                        to_sleep = self._normal_scene_handler.interval_seconds - past_time
                    else:
                        ops = self._normal_scene_handler.get_operations(trigger_time)
                        if ops is not None:
                            self._running_task = OperationTask(ops)
                            self._event_trigger_time[''] = trigger_time
                            future = self._running_task.run_async()

                if to_sleep is not None:
                    time.sleep(to_sleep)
                elif future is not None:
                    try:
                        future.result()
                    except Exception:  # run_async里有callback打印日志
                        pass
                else:
                    time.sleep(0.02)

    def _on_event(self, event: ContextEventItem):
        event_id = event.event_id
        if event_id not in self._event_to_scene_handler:
            return

        future: Future = _od_conditional_op_executor.submit(self._handle_trigger_event, event)
        future.add_done_callback(thread_utils.handle_future_result)

    def _handle_trigger_event(self, event: ContextEventItem) -> None:
        """
        处理触发器事件
        :param event:
        :return:
        """
        event_id = event.event_id
        trigger_time: float = event.data
        log.debug('场景触发 %s', event.event_id)
        handler = self._event_to_scene_handler[event_id]

        # 上锁后判断是否新建任务
        with self._task_lock:
            if not self._running:
                return
            last_trigger_time = self._event_trigger_time.get(event_id, 0)
            if trigger_time - last_trigger_time <= handler.interval_seconds:  # 冷却时间没过 不触发
                return

            ops = handler.get_operations(trigger_time)
            if ops is not None:  # 必须要先增加计算器 避免无触发场景的循环进行
                self._running_trigger_cnt.inc()

            if self._running_task is not None:
                self._running_task.stop()
                self._running_trigger_cnt.dec()

            if ops is not None:
                self._running_task = OperationTask(ops)
                self._event_trigger_time[event_id] = trigger_time
                self._running_task.run_async()

    def stop_running(self) -> None:
        """
        停止执行
        :return:
        """
        if self.event_bus is not None:
            self.event_bus.unlisten_all_event(self)

        # 上锁后停止 防止依然有新建任务
        with self._task_lock:
            self._running = False
            if self._running_task is not None:
                self._running_task.stop()
