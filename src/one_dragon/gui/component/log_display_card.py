import logging
from typing import List, Optional

from PySide6.QtCore import Signal, QObject
from qfluentwidgets import PlainTextEdit

from one_dragon.utils.log_utils import log


class LogSignal(QObject):

    new_log = Signal(str)

    def on_log(self, full_log: str):
        self.new_log.emit(full_log)


class LogReceiver(logging.Handler):

    def __init__(self, signal: LogSignal):
        logging.Handler.__init__(self)

        self.signal: LogSignal = signal
        self.log_list: List[str] = []

    def emit(self, record):
        msg = self.format(record)
        self.log_list.append(msg)
        if len(self.log_list) > 50:
            self.log_list.pop(0)
        self.signal.on_log('\n'.join(self.log_list))


class LogDisplayCard(PlainTextEdit):

    def __init__(self, parent=None, max_height: Optional[int] = None):
        super().__init__(parent=parent)
        if max_height is not None:
            self.setMaximumHeight(max_height)

        self.update_on_log: bool = False  # 在接收到log的时候更新

        self.log_signal = LogSignal()
        self.log_signal.new_log.connect(self.on_log)
        self.receiver = LogReceiver(self.log_signal)
        log.addHandler(self.receiver)

    def on_log(self, full_log: str) -> None:
        """
        日志出现时更新
        :param full_log:
        :return:
        """
        if not self.update_on_log:
            return
        self.setPlainText(full_log)

        # 滚动到最下面
        scroll_bar = self.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
