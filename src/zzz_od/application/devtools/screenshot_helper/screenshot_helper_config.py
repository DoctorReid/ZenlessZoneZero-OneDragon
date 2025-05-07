from one_dragon.base.config.yaml_config import YamlConfig


class ScreenshotHelperConfig(YamlConfig):

    def __init__(self, instance_idx: int):
        YamlConfig.__init__(self, 'screenshot_helper', instance_idx=instance_idx)

    @property
    def frequency_second(self) -> float:
        return self.get('frequency_second', 0.1)

    @frequency_second.setter
    def frequency_second(self, new_value: float) -> None:
        self.update('frequency_second', new_value)

    @property
    def length_second(self) -> float:
        return self.get('length_second', 1)

    @length_second.setter
    def length_second(self, new_value: float) -> None:
        self.update('length_second', new_value)

    @property
    def key_save(self) -> int:
        return self.get('key_save', '1')

    @key_save.setter
    def key_save(self, new_value: str) -> None:
        self.update('key_save', new_value)

    @property
    def dodge_detect(self) -> bool:
        return self.get('dodge_detect', True)

    @dodge_detect.setter
    def dodge_detect(self, new_value: bool) -> None:
        self.update('dodge_detect', new_value)

    @property
    def screenshot_before_key(self) -> bool:
        return self.get('screenshot_before_key', True)

    @screenshot_before_key.setter
    def screenshot_before_key(self, new_value: bool) -> None:
        self.update('screenshot_before_key', new_value)
