from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord
from zzz_od.application.hollow_zero.hollow_zero_config import HollowZeroConfig


class HollowZeroRunRecord(AppRunRecord):

    def __init__(self, config: HollowZeroConfig, instance_idx: Optional[int] = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(
            self,
            'hollow_zero',
            instance_idx=instance_idx,
            game_refresh_hour_offset=game_refresh_hour_offset
        )
        self.config: HollowZeroConfig = config

    @property
    def run_status_under_now(self):
        """
        基于当前时间显示的运行状态
        :return:
        """
        if self._should_reset_by_dt():
            return AppRunRecord.STATUS_WAIT
        elif self.weekly_run_times >= self.config.weekly_times:
            return AppRunRecord.STATUS_SUCCESS
        else:
            return self.run_status

    def reset_record(self) -> None:
        AppRunRecord.reset_record(self)
        self.weekly_run_times = 0

    @property
    def weekly_run_times(self) -> int:
        return self.get('weekly_run_times', 0)

    @weekly_run_times.setter
    def weekly_run_times(self, new_value: int) -> None:
        self.update('weekly_run_times', new_value)

    def add_times(self) -> None:
        """
        增加通关次数
        :return:
        """
        self.weekly_run_times = self.weekly_run_times + 1

    def is_finished_by_times(self) -> bool:
        """
        从运行次数看 是否已经完成了
        :return:
        """
        return self.weekly_run_times >= self.config.weekly_times
