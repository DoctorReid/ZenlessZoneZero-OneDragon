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
    def key_normal_attack(self) -> str:
        return self.get('key_normal_attack', 'mouse_left')

    @key_normal_attack.setter
    def key_normal_attack(self, new_value: str) -> None:
        self.update('key_normal_attack', new_value)

    @property
    def key_dodge(self) -> str:
        return self.get('key_dodge', 'shift')

    @key_dodge.setter
    def key_dodge(self, new_value: str) -> None:
        self.update('key_dodge', new_value)

    @property
    def key_switch_next(self) -> str:
        return self.get('key_switch_next', 'space')

    @key_switch_next.setter
    def key_switch_next(self, new_value: str) -> None:
        self.update('key_switch_next', new_value)

    @property
    def key_switch_prev(self) -> str:
        return self.get('key_switch_prev', 'c')

    @key_switch_prev.setter
    def key_switch_prev(self, new_value: str) -> None:
        self.update('key_switch_prev', new_value)

    @property
    def key_special_attack(self) -> str:
        return self.get('key_special_attack', 'e')

    @key_special_attack.setter
    def key_special_attack(self, new_value: str) -> None:
        self.update('key_special_attack', new_value)

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
