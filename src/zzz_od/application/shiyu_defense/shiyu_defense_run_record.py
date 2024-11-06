from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord


class CriticalNode:

    def __init__(self, node_cnt: int, start_dt: str, end_dt: str):
        """
        剧变节点
        """
        self.node_cnt: int = node_cnt  # 节点数
        self.start_dt: str = start_dt  # 开始时间
        self.end_dt: str = end_dt  # 结束时间


class ShiyuDefenseRunRecord(AppRunRecord):

    def __init__(self, instance_idx: Optional[int] = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(
            self,
            'shiyu_defense',
            instance_idx=instance_idx,
            game_refresh_hour_offset=game_refresh_hour_offset
        )

        self.critical_nodes: list[CriticalNode] = [
            CriticalNode(7, '20241016', '20241031'),
            CriticalNode(7, '20241101', '20241115'),
        ]

    @property
    def run_status_under_now(self):
        """
        基于当前时间显示的运行状态
        :return:
        """
        next_node_idx = self.next_node_idx()
        current_node = self.current_dt_node()
        if next_node_idx is None or current_node is None:
            return AppRunRecord.STATUS_SUCCESS
        elif self._should_reset_by_dt():
            return AppRunRecord.STATUS_WAIT
        else:
            return self.run_status

    def current_dt_node(self) -> Optional[CriticalNode]:
        """
        当前日期下的剧变节点
        """
        current_dt = self.get_current_dt()
        for node in self.critical_nodes:
            if node.start_dt <= current_dt <= node.end_dt:
                return node

    def next_node_idx(self) -> Optional[int]:
        """
        当前日期下
        下一个需要挑战的节点下标
        """
        current_node = self.current_dt_node()
        if current_node is None:
            return None

        history = self.get(current_node.start_dt, [])
        for i in range(1, current_node.node_cnt + 1):
            if i not in history:
                return i

    def add_node_finished(self, node_idx: int) -> None:
        """
        将某个节点加入完成
        @param node_idx:
        @return:
        """
        current_node = self.current_dt_node()
        if current_node is None:
            return

        history = self.get(current_node.start_dt, [])

        # 删除旧的记录
        for node in self.critical_nodes:
            if node.start_dt != current_node.start_dt and node.start_dt in self.data:
                self.data.pop(node.start_dt)

        if node_idx not in history:
            history.append(node_idx)
            self.data[current_node.start_dt] = history
            self.save()
