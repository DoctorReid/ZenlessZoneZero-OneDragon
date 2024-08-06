from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord


class NotoriousHuntRunRecord(AppRunRecord):

    def __init__(self, instance_idx: Optional[int] = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(
            self,
            'notorious_hunt',
            instance_idx=instance_idx,
            game_refresh_hour_offset=game_refresh_hour_offset
        )

    def reset_record(self) -> None:
        AppRunRecord.reset_record(self)
        self.left_times = 0

    @property
    def left_times(self) -> int:
        return self.get('left_times', 3)

    @left_times.setter
    def left_times(self, new_value: int) -> None:
        self.update('left_times', new_value)

