from typing import ClassVar

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_def import OperationDef
from zzz_od.context.custom_battle_context import CustomBattleContext


class AtomicSetState(AtomicOp):

    OP_NAME: ClassVar[str] = '设置状态'

    def __init__(self, ctx: CustomBattleContext, op_def: OperationDef):
        self.ctx: CustomBattleContext = ctx
        self.event_id: str = op_def.state_name
        self.diff_time: float = op_def.state_seconds
        self.value: int = op_def.state_value
        self.value_add: int = op_def.state_value_add

        if op_def.data is not None:
            if len(op_def.data) > 0:
                self.event_id = op_def.data[0]
            if len(op_def.data) > 1:
                self.diff_time = float(op_def.data[1])
            if len(op_def.data) > 2:
                self.value = int(op_def.data[2])

        AtomicOp.__init__(self, op_name='%s %s' % (AtomicSetState.OP_NAME,self.event_id))

    def execute(self):
        self.ctx.set_state(self.event_id, self.diff_time, self.value, self.value_add)
