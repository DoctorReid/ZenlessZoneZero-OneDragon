from PySide6.QtCore import QObject, Signal


class ContextEventSignal(QObject):

    instance_changed = Signal()

    def __init__(self):
        QObject.__init__(self)
