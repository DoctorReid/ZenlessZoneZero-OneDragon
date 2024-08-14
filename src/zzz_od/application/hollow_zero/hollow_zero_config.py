from typing import Optional

from one_dragon.base.config.yaml_config import YamlConfig


class HollowZeroConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name='hollow_zero',
            instance_idx=instance_idx,
        )

    @property
    def mission_name(self) -> str:
        return self.get('mission_name', '旧都列车-内部')

    @mission_name.setter
    def mission_name(self, new_value: str):
        self.update('mission_name', new_value)

    @property
    def challenge_config(self) -> str:
        return self.get('challenge_config', None)

    @challenge_config.setter
    def challenge_config(self, new_value: str):
        self.update('challenge_config', new_value)
