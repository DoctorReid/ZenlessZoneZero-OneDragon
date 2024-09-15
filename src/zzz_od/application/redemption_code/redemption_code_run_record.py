from typing import Optional, List

from one_dragon.base.operation.application_run_record import AppRunRecord


class RedemptionCode:

    def __init__(self, code: str, end_dt: str):
        self.code: str = code  # 兑换码
        self.end_dt = end_dt  # 失效日期


class RedemptionCodeRunRecord(AppRunRecord):

    def __init__(self, instance_idx: Optional[int] = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(
            self,
            'redemption_code',
            instance_idx=instance_idx,
            game_refresh_hour_offset=game_refresh_hour_offset
        )

        self.valid_code_list = [
            RedemptionCode('ZZZ888', '20480101'),  # 开服兑换码
            RedemptionCode('ZZZ20240704', '20480101'),  # 开服兑换码
            RedemptionCode('TOURDEINFERNO', '20240914'),  # 1.2前瞻
        ]

    @property
    def run_status_under_now(self):
        current_dt = self.get_current_dt()
        unused_code_list = self.get_unused_code_list(current_dt)
        if len(unused_code_list) > 0:
            return AppRunRecord.STATUS_WAIT
        elif self._should_reset_by_dt():
            return AppRunRecord.STATUS_WAIT
        else:
            return self.run_status

    def check_and_update_status(self):
        current_dt = self.get_current_dt()
        unused_code_list = self.get_unused_code_list(current_dt)
        if len(unused_code_list) > 0:
            self.reset_record()
        else:
            AppRunRecord.check_and_update_status(self)

    @property
    def used_code_list(self) -> List[str]:
        """
        已使用的兑换码
        :return:
        """
        return self.get('used_code_list', [])

    @used_code_list.setter
    def used_code_list(self, new_value: List[str]) -> None:
        """
        已使用的兑换码
        :return:
        """
        self.update('used_code_list', new_value)

    def get_unused_code_list(self, dt: str) -> List[str]:
        """
        按日期获取未使用的兑换码
        :return:
        """
        valid_code_list = [
            i.code
            for i in self.valid_code_list
            if i.end_dt >= dt
        ]
        
        for used in self.used_code_list:
            if used in valid_code_list:  # 先检查是否存在
                valid_code_list.remove(used)
        
        return valid_code_list

    def add_used_code(self, code: str) -> None:
        used = self.used_code_list
        used.append(code)
        self.used_code_list = used
