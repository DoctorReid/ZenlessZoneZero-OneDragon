from typing import ClassVar, List

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_def import OperationDef
from zzz_od.auto_battle.auto_battle_custom_context import AutoBattleCustomContext


class AtomicSetState(AtomicOp):

    OP_NAME: ClassVar[str] = '设置状态'

    def __init__(self, ctx: AutoBattleCustomContext, op_def: OperationDef):
        self.ctx: AutoBattleCustomContext = ctx
        self.state_name: str = op_def.state_name
        self.state_name_list: List[str] = op_def.state_name_list
        self.diff_time: float = op_def.state_seconds
        self.value: int = op_def.state_value
        self.value_add: int = op_def.state_value_add

        if op_def.data is not None:
            if len(op_def.data) > 0:
                self.state_name = op_def.data[0]
            if len(op_def.data) > 1:
                self.diff_time = float(op_def.data[1])
            if len(op_def.data) > 2:
                self.value = int(op_def.data[2])

        AtomicOp.__init__(self, op_name='%s %s' % (AtomicSetState.OP_NAME,self.state_name))

    def execute(self):
        if self.state_name_list is not None:
            self.ctx.set_state(self.state_name_list, self.diff_time, self.value, self.value_add)
        else:
            self.ctx.set_state([self.state_name], self.diff_time, self.value, self.value_add)
