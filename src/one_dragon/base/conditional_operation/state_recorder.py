from typing import Optional

from one_dragon.base.operation.context_event_bus import ContextEventBus, ContextEventItem


class StateRecorder:

    def __init__(self, event_bus: Optional[ContextEventBus], state_name: str):
        self.event_bus: ContextEventBus = event_bus
        self.state_name: str = state_name

        self.last_record_time: float = 0  # 上次记录这个状态的时间

        if self.event_bus is not None:
            self.event_bus.listen_event(state_name, self._on_state_event)

    def _on_state_event(self, event: ContextEventItem):
        """
        状态事件被触发时 记录触发的时间
        :param event:
        :return:
        """
        self.last_record_time = event.data

    def dispose(self) -> None:
        """
        销毁时 解绑事件
        :return:
        """
        self.event_bus.unlisten_all_event(self)
