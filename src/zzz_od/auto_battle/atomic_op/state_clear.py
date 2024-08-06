from typing import ClassVar

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from zzz_od.context.custom_battle_context import CustomBattleContext


class AtomicClearState(AtomicOp):

    OP_NAME: ClassVar[str] = '清除状态'

    def __init__(self, ctx: CustomBattleContext, event_id: str):
        AtomicOp.__init__(self, op_name=AtomicClearState.OP_NAME)
        self.ctx: CustomBattleContext = ctx
        self.event_id: str = event_id

    def execute(self):
        self.ctx.clear_state(self.event_id)
