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

_od_conditional_op_executor = ThreadPoolExecutor(thread_name_prefix='od_conditional_op', max_workers=32)


class ConditionalOperator(YamlConfig):

    def __init__(self, sub_dir: str, template_name: str,
                 instance_idx: Optional[int] = None, is_mock: bool = False):
        YamlConfig.__init__(
            self,
            module_name=template_name,
            sub_dir=[sub_dir],
            instance_idx=instance_idx,
            sample=True, copy_from_sample=False, is_mock=is_mock
        )

        self._inited: bool = False  # 是否已经完成初始化

        self.event_bus: Optional[ContextEventBus] = None
        self._event_to_scene_handler: dict[str, SceneHandler] = {}  # 需要状态触发的场景处理
        self._event_trigger_time: dict[str, float] = {}  # 触发时间
        self._normal_scene_handler: Optional[SceneHandler] = None  # 不需要状态触发的场景处理
        self._running: bool = False  # 整体是否正在运行

        self._task_lock: Lock = Lock()
        self._running_task: Optional[OperationTask] = None  # 正在运行的任务
        self._running_task_cnt: AtomicInt = AtomicInt()

    def init(
            self,
            event_bus: ContextEventBus,
            state_getter: Callable[[str], StateRecorder],
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
            handler = construct_scene_handler(scene_data, state_getter,
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
            log.error('自动指令 [ %s ] 未完成初始化 无法运行', self.module_name)
            return False
        if self._running:
            return False

        self._running = True
        self._running_task_cnt.set(0)  # 每次重置计数器 防止有bug导致无法正常运行

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
        while self._running:
            if self._running_task_cnt.get() > 0:
                # 有其它场景在运行 等待
                time.sleep(0.02)
            else:
                to_sleep: Optional[float] = None

                # 上锁后确保运行状态不会被篡改
                with self._task_lock:
                    if not self._running:
                        # 已经被stop_running中断了 不继续
                        break

                    trigger_time = time.time()
                    last_trigger_time = self._event_trigger_time.get('', 0)
                    past_time = trigger_time - last_trigger_time
                    if past_time < self._normal_scene_handler.interval_seconds:
                        to_sleep = self._normal_scene_handler.interval_seconds - past_time
                    else:
                        ops = self._normal_scene_handler.get_operations(trigger_time)
                        if ops is not None:
                            self._running_task = OperationTask(False, ops)
                            self._event_trigger_time[''] = trigger_time
                            self._running_task_cnt.inc()
                            future = self._running_task.run_async()
                            future.add_done_callback(self._on_task_done)

                if to_sleep is not None:
                    # 等待时间不能写在锁里 要尽快释放锁
                    time.sleep(to_sleep)
                else:  # 没有命中的状态 或者 提交执行了 那就自旋等待
                    time.sleep(0.02)

    def _on_event(self, event: ContextEventItem):
        """
        事件触发
        :param event:
        :return:
        """
        event_id = event.event_id
        if event_id not in self._event_to_scene_handler:
            return

        # 由自己的线程处理事件 避免卡住事件线程
        future: Future = _od_conditional_op_executor.submit(self._handle_trigger_event, event)
        future.add_done_callback(thread_utils.handle_future_result)

    def _handle_trigger_event(self, event: ContextEventItem) -> None:
        """
        处理触发器事件
        :param event:
        :return:
        """
        event_id = event.event_id
        log.debug('场景触发 %s', event.event_id)
        handler = self._event_to_scene_handler[event_id]

        # 上锁后确保运行状态不会被篡改
        with self._task_lock:
            if not self._running:
                # 已经被stop_running中断了 不继续
                return

            trigger_time: float = time.time()  # 这里不应该使用事件发生时间 而是应该使用当前的实际操作时间
            last_trigger_time = self._event_trigger_time.get(event_id, 0)
            if trigger_time - last_trigger_time < handler.interval_seconds:  # 冷却时间没过 不触发
                return

            ops = handler.get_operations(trigger_time)
            # 若ops为空，即无匹配state，则不打断当前task
            if ops is None:
                return

            can_interrupt: bool = False
            if self._running_task is not None:
                old_priority = self._running_task.priority
                new_priority = handler.priority
                if old_priority is None:  # 当前运行场景可随意打断
                    can_interrupt = True
                elif new_priority is not None and new_priority > old_priority:  # 新触发场景优先级更高
                    can_interrupt = True
            else:
                can_interrupt = True

            if not can_interrupt:  # 当前运行场景无法被打断
                return

            # 必须要先增加计算器 避免无触发场景的循环进行
            self._running_task_cnt.inc()
            # 停止已有的操作
            self._stop_running_task()

            self._running_task = OperationTask(True, ops, priority=handler.priority)
            self._event_trigger_time[event_id] = trigger_time
            future = self._running_task.run_async()
            future.add_done_callback(self._on_task_done)

    def stop_running(self) -> None:
        """
        停止执行
        :return:
        """
        if self.event_bus is not None:
            self.event_bus.unlisten_all_event(self)

        # 上锁后停止 上锁后确保运行状态不会被篡改
        with self._task_lock:
            self._running = False
            self._stop_running_task()

    def _stop_running_task(self) -> None:
        """
        停止正在运行的任务
        :return:
        """
        if self._running_task is not None:
            finish = self._running_task.stop()  # stop之前是否已经完成所有op
            if not finish:
                # 如果 finish=True 则计数器已经在 _on_task_done 减少了 这里就不减了
                # 如果 finish=False 则代表还有操作在继续。在这里要减少计数器而不是等_on_task_done 让无触发器场景尽早运行
                self._running_task_cnt.dec()

    def _on_task_done(self, future: Future) -> None:
        """
        一系列指令任务完成后
        """
        with self._task_lock:  # 上锁 保证_running_trigger_cnt安全
            try:
                result = future.result()
                if result:  # 顺利执行完毕
                    self._running_task_cnt.dec()
            except Exception:  # run_async里有callback打印日志
                pass

    def get_usage_states(self) -> set[str]:
        """
        获取使用的状态 需要init之后使用
        :return:
        """
        states: set[str] = set()
        if self._normal_scene_handler is not None:
            states = states.union(self._normal_scene_handler.get_usage_states())
        if self._event_to_scene_handler is not None:
            for handler in self._event_to_scene_handler.values():
                states = states.union(handler.get_usage_states())
        return states
