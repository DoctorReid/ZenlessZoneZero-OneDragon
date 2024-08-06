import time

from typing import ClassVar

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from zzz_od.context.custom_battle_context import CustomBattleContext


class AtomicSetState(AtomicOp):

    OP_NAME: ClassVar[str] = '设置状态'

    def __init__(self, ctx: CustomBattleContext, event_id: str, diff_time: float, value: int):
        AtomicOp.__init__(self,
                          op_name='%s %s %.2f %s' % (
                              AtomicSetState.OP_NAME,
                              event_id,
                              diff_time,
                              value)
                          )
        self.ctx: CustomBattleContext = ctx
        self.event_id: str = event_id
        self.diff_time: float = diff_time
        self.value: int = value

    def execute(self):
        self.ctx.set_state(self.event_id, self.diff_time, self.value)
