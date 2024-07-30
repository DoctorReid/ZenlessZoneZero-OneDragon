from typing import Optional

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from zzz_od.context.battle_context import BattleEventEnum
from zzz_od.context.zzz_context import ZContext


class AtomicBtnMoveA(AtomicOp):

    def __init__(self, ctx: ZContext, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            op_name = BattleEventEnum.BTN_MOVE_A.value + '按下'
        elif release:
            op_name = BattleEventEnum.BTN_MOVE_A.value + '松开'
        else:
            op_name = BattleEventEnum.BTN_MOVE_A.value
        AtomicOp.__init__(self, op_name=op_name, async_op=press and press_time is None)
        self.ctx: ZContext = ctx
        self.press: bool = press
        self.press_time: Optional[float] = press_time
        self.release: bool = release

    def execute(self):
        self.ctx.battle.move_a(self.press, self.press_time, self.release)

    def stop(self) -> None:
        if self.press:
            self.ctx.battle.move_a(release=True)
