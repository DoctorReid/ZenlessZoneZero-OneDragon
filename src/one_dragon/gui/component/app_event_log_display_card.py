from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QVBoxLayout, QSizePolicy
from qfluentwidgets import PlainTextEdit
from typing import List, Optional

from one_dragon.base.operation.context_event_bus import ContextEventBus, ContextEventItem


class EventSignal(QObject):

    event_log = Signal(str)

    def __init__(self,
                 event_bus: ContextEventBus,
                 target_event_ids: List[str],
                 max_size: int = 50):
        QObject.__init__(self)

        self.event_bus: ContextEventBus = event_bus
        self.target_event_ids: List[str] = target_event_ids

        self.event_ids: List[str] = []
        self.max_size: int = max_size

    def start_listen(self) -> None:
        """
        开始监听事件
        :return:
        """
        for event_id in self.target_event_ids:
            self.event_bus.listen_event(event_id, self.on_event)

    def stop_listen(self) -> None:
        """
        停止监听事件
        :return:
        """
        self.event_bus.unlisten_all_event(self)

    def on_event(self, event: ContextEventItem):
        self.event_ids.append(event.event_id)
        if len(self.event_ids) > 50:
            self.event_ids.pop(0)

        self.event_log.emit('\n'.join(self.event_ids))


class AppEventLogDisplayCard(PlainTextEdit):

    def __init__(self, event_bus: ContextEventBus,
                 target_event_ids: List[str],
                 parent=None):
        super().__init__(parent=parent)
        _ = QVBoxLayout(self)  # 创建内部的 QVBoxLayout 以允许高度自动扩展
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.event_signal = EventSignal(event_bus, target_event_ids)
        self.event_signal.event_log.connect(self.update_log)

        # self.setDisabled(True)  # disable之后无法选中文本 也无法滚动
        self.setReadOnly(True)

    def update_log(self, full_log: str) -> None:
        """
        日志出现时更新
        :param full_log:
        :return:
        """
        self.setPlainText(full_log)

        # 滚动到最下面
        scroll_bar = self.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def start_listen(self) -> None:
        """
        开始监听事件
        :return:
        """
        self.event_signal.start_listen()

    def stop_listen(self) -> None:
        """
        停止监听事件
        :return:
        """
        self.event_signal.stop_listen()
