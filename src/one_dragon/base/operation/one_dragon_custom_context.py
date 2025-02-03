from one_dragon.custom.custom_config import CustomConfig


class OneDragonCustomContext:

    def __init__(self):
        self.custom_config: CustomConfig = CustomConfig()

    def init_by_config(self) -> None:
        pass