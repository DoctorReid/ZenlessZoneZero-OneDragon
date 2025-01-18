from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord, AppRunRecordPeriod
from zzz_od.application.hollow_zero.lost_void.lost_void_config import LostVoidConfig, LostVoidExtraTask


class LostVoidRunRecord(AppRunRecord):

    def __init__(self, config: LostVoidConfig, instance_idx: Optional[int] = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(
            self,
            'lost_void',
            instance_idx=instance_idx,
            game_refresh_hour_offset=game_refresh_hour_offset,
            record_period=AppRunRecordPeriod.WEEKLY
        )

        self.config: LostVoidConfig = config

    @property
    def daily_run_times(self) -> int:
        return self.get('daily_run_times', 0)

    @daily_run_times.setter
    def daily_run_times(self, new_value: int):
        self.update('daily_run_times', new_value)

    @property
    def weekly_run_times(self) -> int:
        return self.get('weekly_run_times', 0)

    @weekly_run_times.setter
    def weekly_run_times(self, new_value: int):
        self.update('weekly_run_times', new_value)

    def add_complete_times(self) -> None:
        """
        每周和每天都增加一次完成次数
        @return:
        """
        self.daily_run_times += 1
        self.weekly_run_times += 1

    @property
    def eval_point_complete(self) -> bool:
        """
        是否已经刷满业绩点
        """
        return self.get('eval_point_complete', False)

    @eval_point_complete.setter
    def eval_point_complete(self, new_value: bool) -> None:
        """
        是否已经刷满业绩点
        """
        self.update('eval_point_complete', new_value)

    @property
    def period_reward_complete(self) -> bool:
        """
        是否已经刷满周期奖励
        """
        return self.get('period_reward_complete', False)

    @period_reward_complete.setter
    def period_reward_complete(self, new_value: bool) -> None:
        """
        是否已经刷满周期奖励
        """
        self.update('period_reward_complete', new_value)

    def is_finished_by_week(self) -> bool:
        """
        按周的角度看是否已经完成
        """
        if self.weekly_run_times < self.config.weekly_plan_times:
            # 基础次数都还没有完成
            return False
        if self.config.extra_task == LostVoidExtraTask.NONE.value.value:
            # 完成基础次数 不需要额外刷取
            return True
        elif self.config.extra_task == LostVoidExtraTask.EVAL_POINT.value.value:
            # 完成基础次数 需要刷业绩 就看空业绩点出来没有
            return self.eval_point_complete
        elif self.config.extra_task == LostVoidExtraTask.PERIOD_REWARD.value.value:
            return self.period_reward_complete
        else:
            return False

    def is_finished_by_day(self) -> bool:
        """
        按天角度看是否已经完成
        """
        if self.is_finished_by_week():
            return True
        elif self.daily_run_times < self.config.daily_plan_times:
            # 基础次数都还没有完成
            return False
        else:
            return True

    def reset_record(self):
        AppRunRecord.reset_record(self)

        self.daily_run_times = 0
        self.weekly_run_times = 0
        self.eval_point_complete = False
        self.period_reward_complete = False