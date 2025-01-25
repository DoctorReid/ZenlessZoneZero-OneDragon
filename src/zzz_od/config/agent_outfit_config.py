from enum import Enum

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig


class AgentOutfitConfig(YamlConfig):

    def __init__(self, instance_idx: int):
        YamlConfig.__init__(self, 'agent_outfit', instance_idx=instance_idx)

    @property
    def nicole(self) -> str:
        return self.get('nicole', AgentOutfitNicole.DEFAULT.value.value)

    @nicole.setter
    def nicole(self, value: str) -> None:
        self.update('nicole', value)

    @property
    def ellen(self) -> str:
        return self.get('ellen', AgentOutfitEllen.DEFAULT.value.value)

    @ellen.setter
    def ellen(self, value: str) -> None:
        self.update('ellen', value)

    @property
    def astra_yao(self) -> str:
        return self.get('astra_yao', AgentOutfitAstraYao.DEFAULT.value.value)

    @astra_yao.setter
    def astra_yao(self, value: str) -> None:
        self.update('astra_yao', value)


class AgentOutfitNicole(Enum):
    """
    妮可皮肤
    """
    DEFAULT = ConfigItem('默认', 'nicole')
    CUNNING_CUTIE = ConfigItem('狡黠甜心', 'nicole_cunning_cutie')


class AgentOutfitEllen(Enum):
    """
    艾莲皮肤
    """
    DEFAULT = ConfigItem('默认', 'ellen')
    ON_CAMPUS = ConfigItem('从周一到周五', 'ellen_on_campus')


class AgentOutfitAstraYao(Enum):
    """
    耀嘉音皮肤
    """
    DEFAULT = ConfigItem('默认', 'astra_yao')
    CHANDELIER = ConfigItem('水晶灯下', 'astra_yao_chandelier')
