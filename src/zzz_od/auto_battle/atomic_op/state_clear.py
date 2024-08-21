from typing import ClassVar

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_def import OperationDef
from zzz_od.context.custom_battle_context import CustomBattleContext


class AtomicClearState(AtomicOp):

    OP_NAME: ClassVar[str] = '清除状态'

    def __init__(self, ctx: CustomBattleContext, op_def: OperationDef):
        AtomicOp.__init__(self, op_name=AtomicClearState.OP_NAME)
        self.ctx: CustomBattleContext = ctx
        self.event_id: str = op_def.state_name
        if op_def.data is not None:
            if len(op_def.data) > 0:
                self.event_id = op_def.data[0]

    def execute(self):
        self.ctx.clear_state(self.event_id)
