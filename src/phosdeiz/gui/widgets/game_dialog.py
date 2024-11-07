from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import QTimer, QPropertyAnimation, QPoint, Qt, QEasingCurve
from PySide6.QtGui import QColor, QFont

from qfluentwidgets import MaskDialogBase, SimpleCardWidget

from ...gui.services import PhosStyleSheet


class GameDialog(MaskDialogBase):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)

        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))

        self.widget = SimpleCardWidget()
        self.viewLayout = QHBoxLayout(self.widget)

        self._hBoxLayout.removeWidget(self.widget)
        self._hBoxLayout.addWidget(self.widget, 1, Qt.AlignCenter)

        self.text = text
        self.labels = []

        for char in self.text:
            label = QLabel(char, self)
            label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
            label.setAlignment(Qt.AlignCenter)
            self.viewLayout.addWidget(label)
            self.labels.append(label)

        self.widget.setFixedWidth(240)

        PhosStyleSheet.GAME_DIALOG.apply(self)

        self.current_index = 0
        self.isAnimtioning = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_text)
        self.timer.start(100)

    def animate_text(self):
        if self.isAnimtioning:
            return
        self.isAnimtioning = True
        self.jump_start()

    def jump_start(self):
        char_label: QLabel = self.labels[self.current_index]
        self.animation = QPropertyAnimation(char_label, b"pos")
        current_pos = char_label.pos()
        self.animation.setStartValue(current_pos)
        self.animation.setEndValue(QPoint(current_pos.x(), current_pos.y() - 5))
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        self.animation.finished.connect(self.jump_end)  # 连接结束动画的槽

        for label in self.labels:
            label.setObjectName("normal")
        char_label.setObjectName("jump")

        PhosStyleSheet.GAME_DIALOG.apply(self)

        self.animation.start()

    def jump_end(self):
        char_label: QLabel = self.labels[self.current_index]
        current_pos = char_label.pos()
        self.animation = QPropertyAnimation(char_label, b"pos")
        self.animation.setStartValue(current_pos)
        self.animation.setEndValue(QPoint(current_pos.x(), current_pos.y() + 5))
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        self.animation.finished.connect(self.update_index)  # 更新索引
        self.animation.start()

    def update_index(self):
        self.current_index = (self.current_index + 1) % len(self.labels)
        self.isAnimtioning = False

    def close_dialog(self):
        # 停止定时器
        self.timer.stop()

        self.close()
