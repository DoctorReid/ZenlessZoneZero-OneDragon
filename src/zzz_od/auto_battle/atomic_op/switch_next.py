from typing import ClassVar

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from zzz_od.context.zzz_context import ZContext


class AtomicSwitchNext(AtomicOp):

    OP_NAME: ClassVar[str] = '按键-切换角色-下一个'

    def __init__(self, ctx: ZContext):
        AtomicOp.__init__(self, op_name=AtomicSwitchNext.OP_NAME)
        self.ctx: ZContext = ctx

    def execute(self):
        self.ctx.switch_next()
