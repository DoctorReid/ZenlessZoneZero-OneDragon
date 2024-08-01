from collections import deque

from PySide6.QtCore import Signal, QObject, QTimer
from PySide6.QtWidgets import QVBoxLayout, QSizePolicy
from qfluentwidgets import PlainTextEdit
from typing import List, Optional

from one_dragon.base.operation.context_event_bus import ContextEventBus, ContextEventItem


class AppEventLogDisplayCard(PlainTextEdit):

    def __init__(self, event_bus: ContextEventBus,
                 target_event_ids: List[str],
                 parent=None):
        super().__init__(parent=parent)
        _ = QVBoxLayout(self)  # 创建内部的 QVBoxLayout 以允许高度自动扩展
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._event_bus: ContextEventBus = event_bus
        self._target_event_ids: List[str] = target_event_ids

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_log)
        self._event_ids: deque = deque(maxlen=50)

        # self.setDisabled(True)  # disable之后无法选中文本 也无法滚动
        self.setReadOnly(True)

    def _update_log(self) -> None:
        """
        日志出现时更新
        :return:
        """
        full_log = '\n'.join(self._event_ids)
        self.setPlainText(full_log)

        # 滚动到最下面
        scroll_bar = self.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def set_update_log(self, to_update: bool) -> None:
        if to_update:
            self.update_timer.stop()
            self.update_timer.start(100)

            self._event_bus.unlisten_all_event(self)
            for event_id in self._target_event_ids:
                self._event_bus.listen_event(event_id, self._on_event)
        else:
            self.update_timer.stop()
            self._event_bus.unlisten_all_event(self)

    def _on_event(self, event: ContextEventItem) -> None:
        self._event_ids.append(event.event_id)
