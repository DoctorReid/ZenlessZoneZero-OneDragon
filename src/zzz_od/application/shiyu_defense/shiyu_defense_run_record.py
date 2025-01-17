from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord
from zzz_od.application.shiyu_defense.shiyu_defense_config import ShiyuDefenseConfig


class CriticalNode:

    def __init__(self, node_cnt: int, start_dt: str, end_dt: str):
        """
        剧变节点
        """
        self.node_cnt: int = node_cnt  # 节点数
        self.start_dt: str = start_dt  # 开始时间
        self.end_dt: str = end_dt  # 结束时间


class ShiyuDefenseRunRecord(AppRunRecord):

    def __init__(self, config: ShiyuDefenseConfig, instance_idx: Optional[int] = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(
            self,
            'shiyu_defense',
            instance_idx=instance_idx,
            game_refresh_hour_offset=game_refresh_hour_offset
        )

        self.config: ShiyuDefenseConfig = config

    @property
    def run_status_under_now(self):
        """
        基于当前时间显示的运行状态
        :return:
        """
        next_node_idx = self.next_node_idx()
        if next_node_idx is None:
            return AppRunRecord.STATUS_SUCCESS
        elif self._should_reset_by_dt():
            return AppRunRecord.STATUS_WAIT
        else:
            return self.run_status

    def next_node_idx(self) -> Optional[int]:
        """
        当前日期下
        下一个需要挑战的节点下标
        """
        history = self.critical_history
        for i in range(1, self.config.critical_max_node_idx + 1):
            if i not in history:
                return i

    def add_node_finished(self, node_idx: int) -> None:
        """
        将某个节点加入完成
        @param node_idx:
        @return:
        """
        history = self.critical_history

        if node_idx not in history:
            history.append(node_idx)
            self.data['critical'] = history
            self.save()

    @property
    def critical_history(self) -> list[int]:
        """
        获取剧变节点完成情况
        """
        return self.get('critical_history', [])

    def reset_record(self):
        AppRunRecord.reset_record(self)

        self.data['critical'] = []
        self.save()
