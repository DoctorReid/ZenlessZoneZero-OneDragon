from collections import deque
import logging
from PySide6.QtCore import Signal, QObject, QTimer
from qfluentwidgets import PlainTextEdit, isDarkTheme
from one_dragon.utils.log_utils import log

class LogSignal(QObject):
    new_log = Signal(str)

class LogReceiver(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_list: deque[str] = deque(maxlen=256)  # 限制最大日志数量
        self.new_logs: list[str] = []  # 存储新日志

    def emit(self, record):
        """将新日志记录添加到日志队列"""
        msg = self.format(record)
        self.log_list.append(msg)
        self.new_logs.append(msg)  # 存储新日志

    def get_new_logs(self) -> list[str]:
        """获取新的日志"""
        new_logs = self.new_logs.copy()  # 返回当前的新日志
        self.new_logs.clear()  # 清空新日志列表
        return new_logs

    def clear_logs(self):
        """清空日志队列"""
        self.log_list.clear()  # 清空日志缓存
        self.new_logs.clear()  # 清空新日志列表


class LogDisplayCard(PlainTextEdit):  # 使用 PlainTextEdit 显示日志
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setReadOnly(True)
        self.init_color()  # 初始化颜色
        self.receiver = LogReceiver()
        log.addHandler(self.receiver)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_logs)

        self.auto_scroll = True  # 控制是否自动滚动
        self.update_frequency = 100  # 更新频率（毫秒）
        self.is_running = False  # 程序是否正在运行
        self.setMaximumBlockCount(128)  # 限制显示行数

    # 根据主题设置颜色
    def init_color(self):
        if isDarkTheme():
            self._color = '#00D9A3'  
        else:
            self._color = '#00A064'

    def set_update_log(self, to_update: bool) -> None:
        """启用或停止日志更新"""
        if to_update:
            self.start()
        else:
            self.stop()
        self.receiver.update_log = to_update

    def start(self):
        """启动日志显示"""
        self.init_color()
        if not self.is_running:
            self.is_running = True
            self.receiver.clear_logs()  # 清空旧日志
            self.clear()  # 清空界面上的日志
            self.auto_scroll = True  # 启用自动滚动
            self.update_timer.start(self.update_frequency)  # 启动定时器

    def stop(self):
        """停止日志显示"""
        if self.is_running:
            self.is_running = False
            self.auto_scroll = False  # 禁用自动滚动
            self.update_timer.stop()  # 停止定时器

    def update_logs(self) -> None:
        """更新日志显示区域"""
        new_logs = self.receiver.get_new_logs()
        if len(new_logs) != 0:
            formatted_logs = self._format_logs(new_logs)  # 格式化日志
            self.appendHtml(formatted_logs)  # 使用 HTML 追加新日志
            if self.auto_scroll:
                self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())  # 滚动到最新位置

    def _format_logs(self, logs: list[str]) -> str:
        """格式化日志"""
        formatted_logs = []
        formatted_log = ""
        
        for log in logs:
            # 给方括号内的内容着色
            if '[' in log and ']' in log:
                start = log.find('[') + 1
                end = log.find(']')
                before = log[:start]
                colored = f'<span style="color: {self._color};">{log[start:end]}</span>'
                after = log[end:]
                formatted_log = before + colored + after
            else:
                formatted_log = log
            formatted_logs.append(formatted_log)

        # 检查是否有日志，并根据数量返回格式化的日志字符串
        if len(logs) <= 1:  # 如果只有一条日志
            return formatted_log  # 直接返回该日志
        else:
            return '<br>'.join(formatted_logs)  # 用 <br> 分隔每条日志
