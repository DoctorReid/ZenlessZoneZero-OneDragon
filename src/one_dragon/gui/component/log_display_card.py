from collections import deque

import logging
from PySide6.QtCore import Signal, QObject, QTimer
from PySide6.QtWidgets import QVBoxLayout
from qfluentwidgets import PlainTextEdit

from one_dragon.utils.log_utils import log


class LogSignal(QObject):

    new_log = Signal(str)


class LogReceiver(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)
        self.log_list: deque[str] = deque(maxlen=50)
        self.update_log: bool = False

    def emit(self, record):
        if not self.update_log:
            return
        msg = self.format(record)
        self.log_list.append(msg)


class LogDisplayCard(PlainTextEdit):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        _ = QVBoxLayout(self)  # 创建内部的 QVBoxLayout 以允许高度自动扩展
        # self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.update_on_log: bool = False  # 在接收到log的时候更新

        self.receiver = LogReceiver()
        log.addHandler(self.receiver)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_log)

        # self.setDisabled(True)  # disable之后无法选中文本 也无法滚动
        self.setReadOnly(True)

    def set_update_log(self, to_update: bool) -> None:
        if to_update:
            self.update_timer.stop()
            self.update_timer.start(100)
        else:
            self.update_timer.stop()
        self.receiver.update_log = to_update

    def _update_log(self) -> None:
        full_log = '\n'.join(self.receiver.log_list)
        self.setPlainText(full_log)

        # 滚动到最下面
        scroll_bar = self.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
