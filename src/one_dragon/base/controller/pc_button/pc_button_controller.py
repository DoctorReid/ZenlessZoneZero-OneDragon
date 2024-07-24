class PcButtonController:

    def __init__(self):
        self.key_press_time: float = 0.02

    def tap(self, key: str) -> None:
        """
        按键
        """
        pass

    def reset(self) -> None:
        """
        重置状态
        """
        pass

    def set_key_press_time(self, key_press_time: float) -> None:
        self.key_press_time = key_press_time
