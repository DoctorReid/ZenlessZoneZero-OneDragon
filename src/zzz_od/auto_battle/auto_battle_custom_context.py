import time

from typing import List

from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.conditional_operation.state_recorder import StateRecord
from zzz_od.context.zzz_context import ZContext


class AutoBattleCustomContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx
        self.auto_op: ConditionalOperator = ConditionalOperator('', '', is_mock=True)

    def init_battle_custom_context(self, auto_op: ConditionalOperator):
        self.auto_op = auto_op

    def set_state(self, state_name_list: List[str], time_diff: float, value: int, value_add: int) -> None:
        """
        设置状态
        :param state_name_list: 状态名称列表
        :param time_diff: 状态设置时间与当前时间的便宜量
        :param value: 状态值
        :param value_add: 状态叠加值
        :return:
        """
        now = time.time()
        self.auto_op.batch_update_states([
            StateRecord(state_name, trigger_time=now + time_diff, value=value, value_to_add=value_add)
            for state_name in state_name_list
        ])

    def clear_state(self, state_name_list: List[str]) -> None:
        """
        清除状态 批量清除可以更快
        :param state_name_list: 状态名称列表
        :return:
        """
        self.auto_op.batch_update_states([
                StateRecord(state_name, is_clear=True)
                for state_name in state_name_list
        ])
