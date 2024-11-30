from typing import ClassVar

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_def import OperationDef
from zzz_od.auto_battle.auto_battle_context import AutoBattleContext


class AtomicSwitchAgent(AtomicOp):

    OP_NAME: ClassVar[str] = '切换角色'

    def __init__(self, ctx: AutoBattleContext, op_def: OperationDef):
        self.ctx: AutoBattleContext = ctx
        self.agent_name: str = op_def.agent_name

        AtomicOp.__init__(self, op_name='%s %s' % (AtomicSwitchAgent.OP_NAME, self.agent_name))

    def execute(self):
        self.ctx.switch_by_name(self.agent_name)

    def stop(self) -> None:
        pass