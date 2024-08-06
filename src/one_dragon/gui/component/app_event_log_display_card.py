from collections import deque

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QSizePolicy
from qfluentwidgets import PlainTextEdit
from typing import List

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
        self._is_update_log: bool = False

        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_log)
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
        self._is_update_log = to_update
        if to_update:
            self._update_timer.stop()
            self._update_timer.start(100)

            self._event_bus.unlisten_all_event(self)
            for event_id in self._target_event_ids:
                self._event_bus.listen_event(event_id, self._on_event)
        else:
            self._update_timer.stop()
            self._event_bus.unlisten_all_event(self)

    def _on_event(self, event: ContextEventItem) -> None:
        self._event_ids.append(event.event_id)

    def set_target_event_ids(self, event_ids: List[str]) -> None:
        """
        更新需要监听的事件
        :param event_ids:
        :return:
        """
        if self._is_update_log:
            # 解除不需要监听的
            for event_id in self._target_event_ids:
                if event_id not in event_ids:
                    self._event_bus.unlisten_event(event_id, self._on_event)
            # 新增监听的
            for event_id in event_ids:
                if event_id not in self._target_event_ids:
                    self._event_bus.listen_event(event_id, self._on_event)

        self._target_event_ids = event_ids
