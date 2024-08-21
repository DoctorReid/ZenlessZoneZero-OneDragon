class StateEvent:

    def __init__(self, trigger_time: float, value: int = None, value_add: int = None):
        self.trigger_time: float = trigger_time
        self.value: int = value
        self.value_add: int = value_add

    def __str__(self):
        return '%.2f %s %s' % (self.trigger_time, self.value, self.value_add)
