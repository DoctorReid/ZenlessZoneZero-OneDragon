import time
from concurrent.futures import ThreadPoolExecutor, Future

from threading import Lock
from typing import Optional, Callable, List

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_def import OperationDef
from one_dragon.base.conditional_operation.operation_task import OperationTask, OperationTaskInfo
from one_dragon.base.conditional_operation.operation_template import OperationTemplate
from one_dragon.base.conditional_operation.scene_handler import SceneHandler
from one_dragon.base.conditional_operation.state_handler_template import StateHandlerTemplate
from one_dragon.base.conditional_operation.state_recorder import StateRecorder, StateRecord
from one_dragon.base.conditional_operation.utils import scenes_handler
from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.thread.atomic_int import AtomicInt
from one_dragon.utils import thread_utils
from one_dragon.utils.log_utils import log

_od_conditional_op_executor = ThreadPoolExecutor(thread_name_prefix='od_conditional_op', max_workers=32)
""" [自动战斗] 线程池,最多支持32个线程 """

# 自动战斗控制器
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

        # —————— 触发器 ——————
        
        self._trigger_states: dict[str, SceneHandler] = {}
        """ [触发器] 触发器 """
        self._normal_trigger: Optional[SceneHandler] = None
        """ [触发器] 不存在条件的触发器,即主线程 """
        self._last_trigger_time: dict[str, float] = {}
        """ [场景] 主线程上次触发时间 """
        
        # —————— 自动战斗 ——————
        
        self.is_running: bool = False
        """ [自动战斗] 自动战斗是否在运行 """
        self._inited: bool = False  
        """ [自动战斗] 是否已经完成初始化 """
        
        # —————— 任务 ——————
        
        self._running_task: Optional[OperationTask] = None
        """ [任务] 当前正在运行的任务 """
        self._task_lock: Lock = Lock()
        """ [任务] 任务锁,可以阻塞任务池的任务执行 """
        self._running_task_cnt: AtomicInt = AtomicInt()
        """ [任务] 任务计数器 """

    def init(
            self,
            op_getter: Callable[[OperationDef], AtomicOp],
            scene_handler_getter: Callable[[str], StateHandlerTemplate],
            operation_template_getter: Callable[[str], OperationTemplate],
    ) -> None:
        """ 初始化 在需要执行之前再使用 """
        
        self._inited = False

        # 初始化自动战斗相关数据
        self.dispose()  
        self._trigger_states: dict[str, SceneHandler] = {}
        self._normal_trigger = None
        self._last_trigger_time = {}

        # yml文件结构:总场景scenes >> 触发器triggers >> 处理器handlers >> 条件集states >> 操作集operations >> 操作op_name
        # 一条龙流程:触发器条件集trigger_states >> 触发器trigger >> 操作集operations >> 任务task
        # 任务池和线程池都最多支持32个线程同时运行
        
        #总场景
        scenes = self.get('scenes', [])

        usage_states = []  # 已经监听的状态变更

        # 从总场景中加载数据,遍历每个触发器
        for data in scenes:
            # 加载触发器
            trigger = scenes_handler(data, self.get_state_recorder,
                                              op_getter, scene_handler_getter, operation_template_getter)
            # 通过触发条件进行归类
            states = data.get('triggers', [])
            if len(states) > 0:
                for state in states:
                    if state in usage_states:
                        raise ValueError('状态监听 %s 出现在多个场景中' % state)
                    self._trigger_states[state] = trigger
            elif self._normal_trigger is not None:
                raise ValueError('存在多个无状态监听的场景')
            # 没有触发条件的触发器作为主线程
            else:
                self._normal_trigger = trigger
        # 初始化完成
        self._inited = True

    def dispose(self) -> None:
        """
        销毁 对子模块进行完全销毁
        :return:
        """
        # 强制停止运行
        self.stop_running()
        # 依次销毁触发器
        if self._trigger_states is not None:
            for _, trigger in self._trigger_states.items():
                 trigger.dispose()
        # 销毁主线程
        if self._normal_trigger is not None:
            self._normal_trigger.dispose()

    def start_running_async(self) -> bool:
        """
        异步启动自动战斗线程
        :return:
        """
        # 自动战斗未初始化时,不运行
        if not self._inited:
            log.error('自动战斗文件[%s]未完成初始化,无法运行', self.module_name)
            return False
        # 有自动战斗在运行时,也不运行
        if self.is_running:
            return False

        # 加载自动战斗相关的参数
        self.is_running = True
        
        # 重置计数器
        self._running_task_cnt.set(0) 

        # 加载主线程,并将主线程提交到线程池
        if self._normal_trigger is not None:
            future: Future = _od_conditional_op_executor.submit(self._normal_trigger_loop)
            future.add_done_callback(thread_utils.handle_future_result)

        return True
    
    # 主线程中,有任务触发后会提交到线程池,并暂停到其他任务完成为止
    def _normal_trigger_loop(self) -> None:
        """
        主循环
        :return:
        """
        while self.is_running:
            # 有其它任务在运行时,等待0.02s后再次循环
            if self._running_task_cnt.get() > 0:
                time.sleep(0.02)
            else:
                # 定义和重置等待时间
                to_sleep: Optional[float] = None

                # 确保其他任务不会被主线程打断
                with self._task_lock:
                    # 自动战斗不在运行时,中断主线程
                    if not self.is_running:
                        break
                    # 触发时间
                    trigger_time: float = time.time()
                    # 上次触发时间
                    last_trigger_time = self._last_trigger_time.get('', 0)
                    # 经过时间
                    past_time = trigger_time - last_trigger_time

                    # 如果经过时间小于间隔时间,则等待到间隔时间为止,此即等待时间
                    if past_time < self._normal_trigger.interval_seconds:
                        to_sleep = self._normal_trigger.interval_seconds - past_time
                    else:
                        # 遍历主线程下的场景,选取第一个符合条件的场景,并加载其[操作集operations]
                        ops,expr = self._normal_trigger.get_operations(trigger_time)
                        if ops is not None:
                            # 将操作集设置为运行中任务
                            self._running_task = OperationTask(False,ops)
                            # 设置页面显示的信息区域数据
                            self._running_task_info =  OperationTaskInfo(trigger="主循环",priority="无优先级",states = expr)
                            # 记录触发时间
                            self._last_trigger_time[''] = trigger_time
                            # 任务计数器+1
                            self._running_task_cnt.inc()
                            # 将任务提交到任务池
                            future = self._running_task.run_async()
                            # 任务完成后回调
                            future.add_done_callback(self._on_task_done)
                
                # 等待时间加载,让主线程在间隔时间后,立刻进行一次循环
                # ps:在有些时候可能主线程的循环时间会小于0.02s,可能是bug
                if to_sleep is not None:
                    time.sleep(to_sleep)
                # 没有等待时间时,按正常的间隔时间循环
                    time.sleep(0.02)

    def _trigger_scene(self, state_name: str) -> None:
        """
        根据触发器条件,检索是否存在满足条件的触发器,并触发其对应的[操作集operations]
        :param state_name: 触发的状态
        :return:
        """
        # 未检索到则返回
        if state_name not in self._trigger_states:
            return
        #检索到则加载处理器
        log.debug('[触发器triggers] | 满足条件: %s', state_name)
        trigger = self._trigger_states[state_name]

        # 如果当前存在任务锁,不进行处理
        with self._task_lock:
            # 自动战斗不在运行时,不进行处理
            if not self.is_running:  
                return
            
            # 触发时间
            trigger_time: float = time.time()
            # 上次触发时间,根据触发的状态进行检索
            last_trigger_time = self._last_trigger_time.get(state_name, 0)
            # 如果经过时间小于间隔时间,则不触发
            if trigger_time - last_trigger_time < trigger.interval_seconds:
                return
            # 若[操作集operations]为空，即未匹配到符合的[条件集states]，不进行处理
            ops,expr = trigger.get_operations(trigger_time)
            if ops is None:
                return

            # 是否能触发
            can_interrupt: bool = False
            # 判断运行中的任务优先级是否比触发任务优先级高
            if self._running_task is not None:
                old_priority = self._running_task.priority
                new_priority = trigger.priority
                # 不存在优先级的任务可以被随意打断
                if old_priority is None:
                    can_interrupt = True
                # 只有高优先度的任务不会被触发任务打断
                elif new_priority is not None and new_priority > old_priority:
                    can_interrupt = True
            else:
                can_interrupt = True

            # 如果can_interrupt为False,不进行处理
            if not can_interrupt:
                return

            # 任务计数器+1,堵塞主循环
            self._running_task_cnt.inc()
            # 停止当前运行的任务
            self._stop_running_task()
            # 将操作集设置为运行中任务
            self._running_task = OperationTask(True, ops, priority=trigger.priority)
            # 设置页面显示的信息区域数据
            self._running_task_info =  OperationTaskInfo(trigger=state_name,priority=trigger.priority,states = expr)
            # 记录触发时间
            self._last_trigger_time[state_name] = trigger_time
            # 将任务提交到任务池
            future = self._running_task.run_async()
            # 任务完成后回调
            future.add_done_callback(self._on_task_done)

    def stop_running(self) -> None:
        """
        停止执行
        :return:
        """
        # 上锁;任务锁会阻止其他方法修改任务计数器
        with self._task_lock:
            self.is_running = False
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
                    self._running_task.priority = None
            except Exception:  # run_async里有callback打印日志
                pass

    def get_usage_states(self) -> set[str]:
        """
        获取使用的状态 需要init之后使用
        :return:
        """
        states: set[str] = set()
        if self._normal_trigger is not None:
            states = states.union(self._normal_trigger.get_usage_states())
        if self._trigger_states is not None:
            for event_id, trigger in self._trigger_states.items():
                states.add(event_id)
                states = states.union(trigger.get_usage_states())
        return states

    def get_state_recorder(self, state_name: str) -> Optional[StateRecorder]:
        """
        如何获取状态记录器 由具体子类实现
        """
        return None

    def update_state(self, state_record: StateRecord) -> None:
        """
        更新一个状态
        然后看是否需要触发对应的场景 清除状态的不进行触发
        :param state_record: 状态记录
        :return:
        """
        # 先统一更新状态值
        state_recorder = self._update_state_recorder(state_record)
        if state_recorder is None:
            return

        # 再去触发具体的场景 由自己的线程处理
        if not state_record.is_clear:
            future: Future = _od_conditional_op_executor.submit(self._trigger_scene, state_recorder.state_name)
            future.add_done_callback(thread_utils.handle_future_result)

    def batch_update_states(self, state_records: List[StateRecord]) -> None:
        """
        批量更新多个状态
        然后看是否需要触发对应的场景 清除状态的不进行触发
        只触发优先级最高的一个
        多个相同优先级时 随机触发一个
        :param state_records: 状态记录列表
        :return:
        """
        top_priority_handler: Optional[SceneHandler] = None
        top_priority_state: Optional[str] = None

        for state_record in state_records:
            state_name = state_record.state_name
            state_recorder = self._update_state_recorder(state_record)
            if state_recorder is None:
                continue
            if state_record.is_clear:
                continue

            # 找优先级最高的场景
            trigger = self._trigger_states.get(state_name)
            if trigger is None:
                continue

            replace = False
            if top_priority_handler is None:
                replace = True
            elif top_priority_handler.priority is None:  # 可随意打断
                replace = True
            elif trigger.priority is None:  # 可随意打断
                pass
            elif trigger.priority > top_priority_handler.priority:  # 新触发场景优先级更高
                replace = True

            if replace:
                top_priority_handler = trigger
                top_priority_state = state_name

        # 触发具体的场景 由自己的线程处理
        if top_priority_state is not None:
            future: Future = _od_conditional_op_executor.submit(self._trigger_scene, top_priority_state)
            future.add_done_callback(thread_utils.handle_future_result)

    def _update_state_recorder(self, new_record: StateRecord) -> Optional[StateRecorder]:
        """
        更新一个状态记录
        :param new_record: 新的状态记录
        :return:
        """
        recorder = self.get_state_recorder(new_record.state_name)
        if recorder is None:
            return

        if new_record.is_clear:
            recorder.clear_state_record()
        else:
            recorder.update_state_record(new_record)
            if recorder.mutex_list is not None:
                for mutex_state in recorder.mutex_list:
                    mutex_recorder = self.get_state_recorder(mutex_state)
                    if mutex_recorder is None:
                        continue
                    mutex_recorder.clear_state_record()

        return recorder
