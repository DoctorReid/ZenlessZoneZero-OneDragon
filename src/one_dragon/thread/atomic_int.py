import threading


class AtomicInt:
    def __init__(self, value=0):
        self.value = value
        self.lock = threading.Lock()

    def get(self):
        with self.lock:
            return self.value

    def set(self, value):
        with self.lock:
            self.value = value

    def inc(self):
        with self.lock:
            self.value += 1
    def dec(self):
        with self.lock:
            self.value -= 1
