from typing import Optional, List

from one_dragon.base.conditional_operation.state_event import StateEvent
from one_dragon.base.operation.context_event_bus import ContextEventItem


class StateRecorder:

    def __init__(self, state_name: str, mutex_list: Optional[List[str]] = None):
        self.state_name: str = state_name
        self.mutex_list: List[str] = mutex_list  # 互斥的状态 这种状态出现的时候 就会将自身状态清空

        self.last_record_time: float = 0  # 上次记录这个状态的时间
        self.last_value: Optional[int] = None  # 上一次记录的值

    def update_state_record(self, event: ContextEventItem) -> None:
        """
        状态事件被触发时 记录触发的时间
        :param event:
        :return:
        """
        data: StateEvent = event.data
        self.last_record_time = data.trigger_time
        if self.last_value is None:
            self.last_value = 0

        if data.value is not None:
            self.last_value = data.value

        if data.value_add is not None:
            self.last_value += data.value_add

    def clear_state_record(self, event: ContextEventItem) -> None:
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
        self.state_name = None
        self.mutex_list = None
        self.last_value = None
        self.last_value = None
