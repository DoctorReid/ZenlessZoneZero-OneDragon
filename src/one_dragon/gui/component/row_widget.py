from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout


class RowWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        self.h_layout = QHBoxLayout(self)

    def add_widget(self, widget: QWidget, stretch: int = 0, alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft):
        self.h_layout.addWidget(widget, stretch=stretch, alignment=alignment)

    def add_stretch(self, stretch: int):
        self.h_layout.addStretch(stretch)
