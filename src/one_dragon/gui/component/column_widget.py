from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout


class ColumnWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        self.row_layout = QVBoxLayout(self)

    def add_widget(self, widget: QWidget, stretch: int = 0, alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignTop):
        self.row_layout.addWidget(widget, stretch=stretch, alignment=alignment)

    def add_stretch(self, stretch: int):
        self.row_layout.addStretch(stretch)
