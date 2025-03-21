from PySide6.QtCore import QObject, Signal


class ContextEventSignal(QObject):

    instance_changed = Signal()
    run_all_apps = Signal()

    def __init__(self):
        QObject.__init__(self)
