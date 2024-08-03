from typing import Optional, List

from one_dragon.base.conditional_operation.state_event import StateEvent
from one_dragon.base.operation.context_event_bus import ContextEventBus, ContextEventItem


class StateRecorder:

    def __init__(self, event_bus: Optional[ContextEventBus],
                 state_name: str, mutex_list: Optional[List[str]] = None):
        self.event_bus: ContextEventBus = event_bus
        self.state_name: str = state_name
        self.mutex_list: List[str] = mutex_list  # 互斥的状态 这种状态出现的时候 就会将自身状态清空

        self.last_record_time: float = 0  # 上次记录这个状态的时间
        self.last_value: Optional[int] = None  # 上一次记录的值

        if self.event_bus is not None:
            self.event_bus.listen_event(state_name, self._on_state_event)

            if self.mutex_list is not None:
                for mutex in self.mutex_list:
                    self.event_bus.listen_event(mutex, self._on_mutex_state_event)

    def _on_state_event(self, event: ContextEventItem) -> None:
        """
        状态事件被触发时 记录触发的时间
        :param event:
        :return:
        """
        data: StateEvent = event.data
        self.last_record_time = data.trigger_time
        self.last_value = data.value

    def _on_mutex_state_event(self, event: ContextEventItem) -> None:
        """
        互斥事件发生时 清空
        """
        self.last_record_time = 0
        self.last_value = None

    def dispose(self) -> None:
        """
        销毁时 解绑事件
        :return:
        """
        self.event_bus.unlisten_all_event(self)
