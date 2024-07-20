from typing import ClassVar

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from zzz_od.context.zzz_context import ZContext


class AtomicDodge(AtomicOp):

    OP_NAME: ClassVar[str] = '按键-闪避'

    def __init__(self, ctx: ZContext):
        AtomicOp.__init__(self, op_name=AtomicDodge.OP_NAME)
        self.ctx: ZContext = ctx

    def execute(self):
        self.ctx.dodge()
