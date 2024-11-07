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
        # 限制日志数量
        self.log_list: deque[str] = deque(maxlen=64)  
        # 新日志
        self.new_logs: list[str] = []
        # 是否接收日志
        self.update = False 

    def emit(self, record):
        """将新日志记录添加到日志队列"""
        # 不接收日志时直接返回
        if not self.update:
            return
        msg = self.format(record)
        self.log_list.append(msg)
        self.new_logs.append(msg)

    def get_new_logs(self) -> list[str]:
        """获取新的日志"""
        new_logs = self.new_logs.copy()
        self.new_logs.clear()
        return new_logs

    def clear_logs(self):
        """清空日志队列"""
        self.log_list.clear()
        self.new_logs.clear()


class LogDisplayCard(PlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        # 设置只读
        self.setReadOnly(True)

        # 初始化颜色
        self.init_color()  

        # 初始化接收器
        self.receiver = LogReceiver()
        log.addHandler(self.receiver)

        # 初始化定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_logs)

        # 设置自动滚动
        self.auto_scroll = False

        # 更新频率（毫秒）
        self.update_frequency = 100 

        # 日志是否运行
        self.is_running = False  

        # 暂停标记
        self.is_pause = False

        # 限制显示行数
        self.setMaximumBlockCount(192)  


    def init_color(self):
        """根据主题设置颜色"""
        if isDarkTheme():
            self._color = '#00D9A3'  
        else:
            self._color = '#00A064'

    def set_update_log(self, update: bool) -> None:
        """启用或停止日志更新"""
        self.receiver.update = update
        self.receiver.clear_logs()
        self.clear()

    def start(self):
        """启动日志显示"""
        self.init_color()
        if not self.is_running:
            self.is_running = True
        if not self.is_pause:
                self.receiver.clear_logs()
                self.clear()
        self.auto_scroll = True
        self.update_timer.start(self.update_frequency)

    def pause(self):
        """停止日志显示"""
        if self.is_running:
            self.is_running = False
        self.is_pause = True
        self.auto_scroll = False
        self.update_timer.stop()

    def stop(self):
        """停止日志显示"""
        if self.is_running:
            self.is_running = False
        if self.is_pause:
            self.is_pause = False
        self.auto_scroll = False
        self.update_timer.stop()

    def update_logs(self) -> None:
        """更新日志显示区域"""
        new_logs = self.receiver.get_new_logs()
        # 格式化日志
        if len(new_logs) != 0:
            formatted_logs = self._format_logs(new_logs)  
            self.appendHtml(formatted_logs)
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

        # 检查是否有日志
        if len(logs) <= 1:
            return formatted_log
        else:
            return '<br>'.join(formatted_logs)
