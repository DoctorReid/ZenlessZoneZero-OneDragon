# coding: utf-8
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QDialog, QPushButton


class ColorInfoDialog(QDialog):

    def __init__(self, color_info: dict, parent: QWidget):
        super().__init__(parent=parent)
        self.setWindowTitle('像素颜色信息')

        pos = color_info.get('pos', (0, 0))
        rgb = color_info.get('rgb', (0, 0, 0))
        hsv = color_info.get('hsv', (0, 0, 0))

        # 颜色预览块
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(60, 60)
        self.color_preview.setStyleSheet(f"background-color: rgb({rgb[0]}, {rgb[1]}, {rgb[2]}); border: 1px solid gray;")

        # 信息文本
        info_text = (f"点击位置: ({pos[0]}, {pos[1]})\n"
                     f"RGB: ({rgb[0]}, {rgb[1]}, {rgb[2]})\n"
                     f"HSV: ({hsv[0]}, {hsv[1]}, {hsv[2]})")
        self.info_label = QLabel(info_text)

        # 内容布局
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        content_layout.addWidget(self.color_preview)
        content_layout.addWidget(self.info_label)

        # 按钮
        self.confirm_button = QPushButton('确定')
        self.confirm_button.clicked.connect(self.accept)

        # 整体布局
        v_layout = QVBoxLayout(self)
        v_layout.addLayout(content_layout)
        v_layout.addWidget(self.confirm_button, 0, Qt.AlignmentFlag.AlignRight)
        self.setLayout(v_layout)