class StateEvent:

    def __init__(self, trigger_time: float, value: int = None):
        self.trigger_time: float = trigger_time
        self.value: int = value