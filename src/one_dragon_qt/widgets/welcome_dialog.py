from PySide6.QtCore import QTimer
from qfluentwidgets import MessageBoxBase, SubtitleLabel, DisplayLabel

class WelcomeDialog(MessageBoxBase):
    """首次运行时显示的欢迎对话框"""

    def __init__(self, parent=None, title="欢迎使用一条龙"):
        super().__init__(parent)

        self.cancelButton.hide()
        self.yesButton.setText("确定(5s)")
        self.yesButton.setEnabled(False)

        self.titleLabel = SubtitleLabel(title)
        self.viewLayout.addWidget(self.titleLabel)

        content_label = DisplayLabel(self)
        content_label.setText("本软件完全<font color='red'>开源 免费</font><br>不要在<font color='red'>第三方渠道</font>购买<br>谨防<font color='red'>诈骗 盗号</font>")

        self.viewLayout.addWidget(content_label)
        self._setup_buttons()
        self._start_countdown()

    def _setup_buttons(self):
        """设置按钮布局 由子类实现"""
        pass

    def _start_countdown(self):
        """启动倒计时"""
        self.countdown_value = 5
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)  # 1秒
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_timer.start()

    def _update_countdown(self):
        """更新确认按钮上的倒计时"""
        self.countdown_value -= 1
        if self.countdown_value > 0:
            self.yesButton.setText(f"确定({self.countdown_value}s)")
        else:
            self.yesButton.setText("确定")
            self.yesButton.setEnabled(True)
            self.countdown_timer.stop()
