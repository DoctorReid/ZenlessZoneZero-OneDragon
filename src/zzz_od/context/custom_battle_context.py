import time

from one_dragon.base.conditional_operation.state_event import StateEvent
from zzz_od.context.zzz_context import ZContext


class CustomBattleContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx

    def set_state(self, event_id: str, time_diff: float, value: int) -> None:
        """
        设置状态
        :param event_id:
        :param time_diff:
        :param value:
        :return:
        """
        now = time.time()
        self.ctx.dispatch_event(event_id, StateEvent(now + time_diff, value))

    def clear_state(self, event_id: str) -> None:
        """
        清除状态
        :param event_id:
        :return:
        """
        self.ctx.dispatch_event(event_id, StateEvent(0))
