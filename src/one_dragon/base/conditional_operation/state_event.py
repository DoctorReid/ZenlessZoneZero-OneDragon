class StateEvent:

    def __init__(self, trigger_time: float, value: int = None):
        self.trigger_time: float = trigger_time
        self.value: int = value

    def __str__(self):
        return '%.2f %s' % (self.trigger_time, self.value)