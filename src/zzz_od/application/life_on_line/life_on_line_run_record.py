from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord
from zzz_od.application.life_on_line.life_on_line_config import LifeOnLineConfig


class LifeOnLineRunRecord(AppRunRecord):

    def __init__(self, config: LifeOnLineConfig,
                 instance_idx: Optional[int] = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(
            self,
            'life_on_line',
            instance_idx=instance_idx,
            game_refresh_hour_offset=game_refresh_hour_offset
        )

        self.config: LifeOnLineConfig = config

    def reset_record(self):
        AppRunRecord.reset_record(self)
        self.daily_run_times = 0

    @property
    def daily_run_times(self) -> int:
        return self.get('daily_run_times', 0)

    @daily_run_times.setter
    def daily_run_times(self, new_value: int) -> None:
        self.update('daily_run_times', new_value)

    def add_times(self) -> None:
        """
        增加通关次数
        :return:
        """
        self.daily_run_times = self.daily_run_times + 1

    def is_finished_by_times(self) -> bool:
        """
        从运行次数看 是否已经完成了
        :return:
        """
        return self.daily_run_times >= self.config.daily_plan_times