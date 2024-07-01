from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout
from qfluentwidgets import Pivot, qrouter


class PivotNavigatorContainer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pivot = Pivot(self)
        self.stacked_widget = QStackedWidget(self)
        self.v_box_layout = QVBoxLayout(self)

        self.v_box_layout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.v_box_layout.addWidget(self.stacked_widget)
        self.v_box_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget.currentChanged.connect(self.on_current_index_changed)

    def add_sub_interface(self, widget: QWidget, text: str):
        self.stacked_widget.addWidget(widget)
        self.pivot.addItem(
            routeKey=widget.objectName(),
            text=text,
            onClick=lambda: self.stacked_widget.setCurrentWidget(widget)
        )

        if self.stacked_widget.currentWidget() is None:
            self.stacked_widget.setCurrentWidget(widget)
        if self.pivot.currentItem() is None:
            self.pivot.setCurrentItem(widget.objectName())

    def on_current_index_changed(self, index):
        widget = self.stacked_widget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stacked_widget, widget.objectName())