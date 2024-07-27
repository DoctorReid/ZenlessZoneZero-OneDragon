from typing import Optional

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from zzz_od.context.battle_context import BattleEventEnum
from zzz_od.context.zzz_context import ZContext


class AtomicBtnNormalAttack(AtomicOp):

    def __init__(self, ctx: ZContext, press_time: Optional[float] = None):
        AtomicOp.__init__(self, op_name=BattleEventEnum.BTN_SWITCH_NORMAL_ATTACK.value)
        self.ctx: ZContext = ctx
        self.press_time: float = press_time  # 持续按键时间

    def execute(self):
        self.ctx.battle.normal_attack(self.press_time)

