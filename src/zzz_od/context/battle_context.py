import time

from cv2.typing import MatLike
from enum import Enum
from typing import Optional

from one_dragon.base.operation.context_event_bus import ContextEventBus
from one_dragon.utils.log_utils import log
from zzz_od.controller.zzz_pc_controller import ZPcController
from zzz_od.game_data.agent import AgentLoader


class BattleEventEnum(Enum):

    BTN_DODGE = '按键-闪避'
    BTN_SWITCH_NEXT = '按键-切换角色-下一个'
    BTN_SWITCH_PREV = '按键-切换角色-上一个'
    BTN_SWITCH_NORMAL_ATTACK = '按键-普通攻击'
    BTN_SWITCH_SPECIAL_ATTACK = '按键-特殊攻击'


class BattleContext:

    def __init__(self, event_bus: ContextEventBus,
                 controller: Optional[ZPcController] = None,
                 agent_loader: Optional[AgentLoader] = None):
        self.__event_bus: ContextEventBus = event_bus

        # 以下都在 ZContext中赋值 在这里只是起一个声明作用
        self.controller: ZPcController = controller
        self.agent_loader: AgentLoader = agent_loader

    def dodge(self):
        e = BattleEventEnum.BTN_DODGE.value
        log.info(e)
        self.controller.dodge()
        self.__event_bus.dispatch_event(e, time.time())

    def switch_next(self):
        e = BattleEventEnum.BTN_SWITCH_NEXT.value
        log.info(e)
        self.controller.switch_next()
        self.__event_bus.dispatch_event(e, time.time())

    def switch_prev(self):
        e = BattleEventEnum.BTN_SWITCH_PREV.value
        log.info(e)
        self.controller.switch_prev()
        self.__event_bus.dispatch_event(e, time.time())

    def normal_attack(self):
        e = BattleEventEnum.BTN_SWITCH_NORMAL_ATTACK.value
        log.info(e)
        self.controller.normal_attack()
        self.__event_bus.dispatch_event(e, time.time())

    def special_attack(self):
        e = BattleEventEnum.BTN_SWITCH_SPECIAL_ATTACK.value
        log.info(e)
        self.controller.special_attack()
        self.__event_bus.dispatch_event(e, time.time())

    def check_character(self, screen: MatLike):
        """
        识别当前画面的角色
        :param screen:
        :return:
        """
        pass
