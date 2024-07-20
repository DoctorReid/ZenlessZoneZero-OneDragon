import time

from enum import Enum

from one_dragon.base.operation.context_event_bus import ContextEventBus
from zzz_od.controller.zzz_pc_controller import ZPcController


class BattleEventEnum(Enum):

    BTN_DODGE = '按键-闪避'
    BTN_SWITCH_NEXT = '按键-切换角色-下一个'
    BTN_SWITCH_PREV = '按键-切换角色-上一个'


class BattleContext:

    def __init__(self, event_bus: ContextEventBus):
        self.__event_bus: ContextEventBus = event_bus
        self.controller: ZPcController = None

    def dodge(self):
        self.controller.dodge()
        self.__event_bus.dispatch_event(BattleEventEnum.BTN_DODGE.value, time.time())

    def switch_next(self):
        self.controller.switch_next()
        self.__event_bus.dispatch_event(BattleEventEnum.BTN_SWITCH_NEXT.value, time.time())

    def switch_prev(self):
        self.controller.switch_prev()
        self.__event_bus.dispatch_event(BattleEventEnum.BTN_SWITCH_PREV.value, time.time())
