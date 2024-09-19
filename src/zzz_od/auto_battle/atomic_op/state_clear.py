from typing import ClassVar

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_def import OperationDef
from zzz_od.auto_battle.auto_battle_custom_context import AutoBattleCustomContext


class AtomicClearState(AtomicOp):

    OP_NAME: ClassVar[str] = '清除状态'

    def __init__(self, ctx: AutoBattleCustomContext, op_def: OperationDef):
        AtomicOp.__init__(self, op_name=AtomicClearState.OP_NAME)
        self.ctx: AutoBattleCustomContext = ctx
        self.state_name: str = op_def.state_name
        if op_def.data is not None:
            if len(op_def.data) > 0:
                self.state_name = op_def.data[0]

    def execute(self):
        self.ctx.clear_state(self.state_name)
