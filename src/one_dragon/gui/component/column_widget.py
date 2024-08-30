from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout


class ColumnWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        self.v_layout = QVBoxLayout(self)

    def add_widget(self, widget: QWidget, stretch: int = 0, alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignTop):
        self.v_layout.addWidget(widget, stretch=stretch, alignment=alignment)

    def add_stretch(self, stretch: int):
        self.v_layout.addStretch(stretch)

    def clear_widgets(self) -> None:
        while self.v_layout.count():
            child = self.v_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
