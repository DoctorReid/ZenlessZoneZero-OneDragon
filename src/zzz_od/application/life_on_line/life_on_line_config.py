from typing import Optional

from one_dragon.base.config.yaml_config import YamlConfig


class LifeOnLineConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name='life_on_line',
            instance_idx=instance_idx,
        )

    @property
    def daily_plan_times(self) -> int:
        return self.get('daily_plan_times', 20)

    @daily_plan_times.setter
    def daily_plan_times(self, new_value: int) -> None:
        self.update('daily_plan_times', new_value)