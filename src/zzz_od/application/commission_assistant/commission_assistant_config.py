from enum import Enum
from typing import Optional

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.gui.component.setting_card.yaml_config_adapter import YamlConfigAdapter


class DialogOptionEnum(Enum):

    FIRST = ConfigItem('第一个')
    LAST = ConfigItem('最后一个')


class CommissionAssistantConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name='commission_assistant',
            instance_idx=instance_idx,
        )

    @property
    def dialog_click_interval(self) -> float:
        return self.get('dialog_click_interval', 0.5)

    @dialog_click_interval.setter
    def dialog_click_interval(self, new_value: float) -> None:
        self.update('dialog_click_interval', new_value)

    @property
    def dialog_click_interval_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'dialog_click_interval', 0.5,
                                 'str', 'float')

    @property
    def dialog_click_when_auto(self) -> bool:
        return self.get('dialog_click_when_auto', False)

    @dialog_click_when_auto.setter
    def dialog_click_when_auto(self, new_value: bool) -> None:
        self.update('dialog_click_when_auto', new_value)

    @property
    def dialog_click_when_auto_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'dialog_click_when_auto', False)

    @property
    def dialog_option(self) -> str:
        return self.get('dialog_option', DialogOptionEnum.LAST.value.value)

    @dialog_option.setter
    def dialog_option(self, new_value: str) -> None:
        self.update('dialog_option', new_value)

    @property
    def dialog_option_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'dialog_option', DialogOptionEnum.LAST.value.value,
                                 'str', 'str')

    @property
    def dodge_config(self) -> str:
        return self.get('dodge_config', '闪避')

    @dodge_config.setter
    def dodge_config(self, new_value: str) -> None:
        self.update('dodge_config', new_value)

    @property
    def dodge_config_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'dodge_config', '闪避',
                                 'str', 'str')

    @property
    def dodge_switch(self) -> str:
        return self.get('dodge_switch', '5')

    @dodge_switch.setter
    def dodge_switch(self, new_value: str) -> None:
        self.update('dodge_switch', new_value)

    @property
    def dodge_switch_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'dodge_switch', '5',
                                 'str', 'str')

    @property
    def auto_battle(self) -> str:
        return self.get('auto_battle', '击破站场-强攻速切')

    @auto_battle.setter
    def auto_battle(self, new_value: str) -> None:
        self.update('auto_battle', new_value)

    @property
    def auto_battle_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'auto_battle', '击破站场-强攻速切',
                                 'str', 'str')

    @property
    def auto_battle_switch(self) -> str:
        return self.get('auto_battle_switch', '6')

    @auto_battle_switch.setter
    def auto_battle_switch(self, new_value: str) -> None:
        self.update('auto_battle_switch', new_value)

    @property
    def auto_battle_switch_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'auto_battle_switch', '6',
                                 'str', 'str')


