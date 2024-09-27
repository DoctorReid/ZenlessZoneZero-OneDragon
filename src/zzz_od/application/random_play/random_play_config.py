from typing import Optional

from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.gui.component.setting_card.yaml_config_adapter import YamlConfigAdapter


class RandomPlayConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name='random_play',
            instance_idx=instance_idx,
        )

    @staticmethod
    def random_agent_name() -> str:
        return '随机'

    @property
    def agent_name(self) -> float:
        return self.get('agent_name', self.random_agent_name())

    @agent_name.setter
    def agent_name(self, new_value: float) -> None:
        self.update('agent_name', new_value)

    @property
    def agent_name_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'agent_name', self.random_agent_name())