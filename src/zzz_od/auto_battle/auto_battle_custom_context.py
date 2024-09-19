import time

from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.conditional_operation.state_recorder import StateRecord
from zzz_od.context.zzz_context import ZContext


class AutoBattleCustomContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx
        self.auto_op: ConditionalOperator = ConditionalOperator('', '', is_mock=True)

    def init_battle_custom_context(self, auto_op: ConditionalOperator):
        self.auto_op = auto_op

    def set_state(self, state_name: str, time_diff: float, value: int, value_add: int) -> None:
        """
        设置状态
        :param state_name: 状态名称
        :param time_diff: 状态设置时间与当前时间的便宜量
        :param value: 状态值
        :param value_add: 状态叠加值
        :return:
        """
        now = time.time()
        self.auto_op.update_state(StateRecord(state_name,
                                              trigger_time=now + time_diff,
                                              value=value,
                                              value_to_add=value_add))

    def clear_state(self, state_name: str) -> None:
        """
        清除状态
        :param state_name: 状态名称
        :return:
        """
        self.auto_op.update_state(StateRecord(state_name, is_clear=True))
