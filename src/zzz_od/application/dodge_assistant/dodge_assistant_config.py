from enum import Enum

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig


class DodgeWayEnum(Enum):

    DODGE = ConfigItem('闪避', 'dodge')
    NEXT = ConfigItem('换人-下一个', 'next')
    PREV = ConfigItem('换人-上一个', 'prev')


class DodgeAssistantConfig(YamlConfig):

    def __init__(self, instance_idx: int):
        YamlConfig.__init__(self, 'dodge_assistant', instance_idx=instance_idx)

    @property
    def dodge_way(self) -> str:
        return self.get('dodge_way', 'dodge')

    @dodge_way.setter
    def dodge_way(self, new_value: str) -> None:
        self.update('dodge_way', new_value)
