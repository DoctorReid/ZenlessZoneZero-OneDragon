from enum import Enum
from typing import Optional

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig


class LostVoidExtraTask(Enum):

    NONE = ConfigItem('不进行')
    EVAL_POINT = ConfigItem('刷满业绩点')
    PERIOD_REWARD = ConfigItem('刷满周期奖励')


class LostVoidConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name='lost_void',
            instance_idx=instance_idx,
        )

    @property
    def daily_plan_times(self) -> int:
        return self.get('daily_plan_times', 0)

    @daily_plan_times.setter
    def daily_plan_times(self, new_value: int):
        self.update('daily_plan_times', new_value)

    @property
    def weekly_plan_times(self) -> int:
        return self.get('weekly_plan_times', 0)

    @weekly_plan_times.setter
    def weekly_plan_times(self, new_value: int):
        self.update('weekly_plan_times', new_value)

    @property
    def extra_task(self) -> str:
        return self.get('extra_task', HollowZeroExtraTask.PERIOD_REWARD.value.value)

    @extra_task.setter
    def extra_task(self, new_value: str):
        self.update('extra_task', new_value)