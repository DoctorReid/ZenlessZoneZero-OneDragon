import threading


class AtomicBool:
    def __init__(self, value: bool = False):
        self._value: bool = value
        self._lock = threading.Lock()

    def get(self):
        with self._lock:
            return self._value

    def set(self, value: bool):
        with self._lock:
            self._value = value

    def set_true(self):
        with self._lock:
            self._value = True

    def set_false(self):
        with self._lock:
            self._value = False
