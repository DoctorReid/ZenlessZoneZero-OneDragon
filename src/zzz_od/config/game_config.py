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
        return self.get('platform', GamePlatformEnum.PC.value.value)

    @platform.setter
    def platform(self, new_value: str) -> None:
        self.update('platform', new_value)

    @property
    def game_language(self) -> str:
        return self.get('game_language', GameLanguageEnum.CN.value.value)

    @game_language.setter
    def game_language(self, new_value: str) -> None:
        self.update('game_language', new_value)

    @property
    def key_attack(self) -> str:
        return self.get('key_attack', 'mouse_left')

    @key_attack.setter
    def key_attack(self, new_value: str) -> None:
        self.update('key_attack', new_value)

    @property
    def key_dodge(self) -> str:
        return self.get('key_dodge', 'mouse_right')

    @key_dodge.setter
    def key_dodge(self, new_value: str) -> None:
        self.update('key_dodge', new_value)

    @property
    def key_change_next(self) -> str:
        return self.get('key_change_next', 'space')

    @key_change_next.setter
    def key_change_next(self, new_value: str) -> None:
        self.update('key_change_next', new_value)

    @property
    def key_change_prev(self) -> str:
        return self.get('key_change_prev', 'c')

    @key_change_prev.setter
    def key_change_prev(self, new_value: str) -> None:
        self.update('key_change_prev', new_value)

    @property
    def key_technique(self) -> str:
        return self.get('key_technique', 'e')

    @key_technique.setter
    def key_technique(self, new_value: str) -> None:
        self.update('key_technique', new_value)

    @property
    def key_ultimate(self) -> str:
        """爆发技"""
        return self.get('key_ultimate', 'e')

    @key_ultimate.setter
    def key_ultimate(self, new_value: str) -> None:
        self.update('key_ultimate', new_value)

    @property
    def key_interact(self) -> str:
        """交互"""
        return self.get('key_interact', 'f')

    @key_interact.setter
    def key_interact(self, new_value: str) -> None:
        self.update('key_interact', new_value)
