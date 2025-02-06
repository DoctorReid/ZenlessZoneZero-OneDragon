from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QLabel


class EllipsisLabel(QLabel):
    def __init__(self, text="", parent=None):
        QLabel.__init__(self, parent)
        self._text = text
        self.setText(text)

    def setText(self, text):
        self._text = text
        self.updateText()

    def resizeEvent(self, event):
        QLabel.resizeEvent(self, event)
        self.updateText()

    def updateText(self):
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self._text, Qt.TextElideMode.ElideRight, self.width())
        QLabel.setText(self, elided)
