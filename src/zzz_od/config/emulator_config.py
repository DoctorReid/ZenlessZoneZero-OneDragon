from enum import Enum

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig

from one_dragon.gui.widgets.setting_card.yaml_config_adapter import YamlConfigAdapter
from one_dragon.module.logger import logger


class GameClient(Enum):
    android_game = ConfigItem('安卓端', 'android')
    cloud_game = ConfigItem('云游戏安卓端', 'cloud_android')


class EmulatorConfig(YamlConfig):
    def __init__(self, instance_idx: int):
        YamlConfig.__init__(self, 'alas', instance_idx=instance_idx)



    @property
    def Alas_Emulator_Serial_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'Alas.Emulator.Serial')

    @property
    def Alas_Emulator_GameClient_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'Alas.Emulator.GameClient')

    @property
    def emulator_path(self) -> str:
        return self.data['Alas']['EmulatorInfo'].get('path', '')

    @emulator_path.setter
    def emulator_path(self, new_value: str) -> None:
        self.data['Alas']['EmulatorInfo']['path'] = new_value
        self.save()
