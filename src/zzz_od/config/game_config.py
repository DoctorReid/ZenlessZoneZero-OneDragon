from enum import Enum

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig


class GamePlatformEnum(Enum):

    PC = ConfigItem('PC')


class GameLanguageEnum(Enum):

    CN = ConfigItem('简体中文', 'cn')




class GameConfig(YamlConfig):

    def __init__(self, instance_idx: int):
        YamlConfig.__init__(self, 'game', instance_idx=instance_idx)

    @property
    def platform(self) -> str:
        return self.get('platform', GamePlatformEnum.value.value)

    @platform.setter
    def platform(self, new_value: str) -> None:
        self.update('platform', new_value)

    @property
    def game_language(self) -> str:
        return self.get('game_language', GameLanguageEnum.value.value)

    @game_language.setter
    def game_language(self, new_value: str) -> None:
        self.update('game_language', new_value)
