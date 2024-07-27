import time
from concurrent.futures import ThreadPoolExecutor

from cv2.typing import MatLike
from enum import Enum
from typing import Optional, List

from one_dragon.utils.log_utils import log
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import Agent, AgentEnum

_battle_check_executor = ThreadPoolExecutor(thread_name_prefix='od_battle_check', max_workers=16)


class BattleEventEnum(Enum):

    BTN_DODGE = '按键-闪避'
    BTN_SWITCH_NEXT = '按键-切换角色-下一个'
    BTN_SWITCH_PREV = '按键-切换角色-上一个'
    BTN_SWITCH_NORMAL_ATTACK = '按键-普通攻击'
    BTN_SWITCH_SPECIAL_ATTACK = '按键-特殊攻击'

    FRONT_ANBY = '前台角色-安比'
    BACK_ANBY = '后台角色-安比'

    FRONT_ANTON = '前台角色-安东'
    BACK_ANTON = '后台角色-安东'

    FRONT_BEN = '前台角色-本'
    BACK_BEN = '后台角色-本'

    FRONT_BILLY = '前台角色-比利'
    BACK_BILLY = '后台角色-比利'

    FRONT_CORIN = '前台角色-可琳'
    BACK_CORIN = '后台角色-可琳'

    FRONT_ELLEN = '前台角色-艾莲'
    BACK_ELLEN = '后台角色-艾莲'

    FRONT_GRACE = '前台角色-格莉丝'
    BACK_GRACE = '后台角色-格莉丝'

    FRONT_KOLEDA = '前台角色-珂蕾妲'
    BACK_KOLEDA = '后台角色-珂蕾妲'

    FRONT_LUCY = '前台角色-露西'
    BACK_LUCY = '后台角色-露西'

    FRONT_LYCAON = '前台角色-莱卡恩'
    BACK_LYCAON = '后台角色-莱卡恩'

    FRONT_NEKOMATA = '前台角色-猫又'
    BACK_NEKOMATA = '后台角色-猫又'

    FRONT_NICOLE = '前台角色-妮可'
    BACK_NICOLE = '后台角色-妮可'

    FRONT_PIPER = '前台角色-派派'
    BACK_PIPER = '后台角色-派派'

    FRONT_RINA = '前台角色-丽娜'
    BACK_RINA = '后台角色-丽娜'

    FRONT_SOLDIER_11 = '前台角色-11号'
    BACK_SOLDIER_11 = '后台角色-11号'

    FRONT_SOUKAKU = '前台角色-苍角'
    BACK_SOUKAKU = '后台角色-苍角'


class BattleContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx

        # 角色列表
        self.agent_list: List[Agent] = []
        self.should_check_all_agents: bool = True  # 是否应该检查所有角色
        self.last_agent_diff_time: Optional[float] = None  # 上一次识别角色不同的时间

    def dodge(self):
        e = BattleEventEnum.BTN_DODGE.value
        log.info(e)
        self.ctx.controller.dodge()
        self.ctx.dispatch_event(e, time.time())

    def switch_next(self):
        e = BattleEventEnum.BTN_SWITCH_NEXT.value
        log.info(e)
        self.ctx.controller.switch_next()
        self.ctx.dispatch_event(e, time.time())

    def switch_prev(self):
        e = BattleEventEnum.BTN_SWITCH_PREV.value
        log.info(e)
        self.ctx.controller.switch_prev()
        self.ctx.dispatch_event(e, time.time())

    def normal_attack(self, press_time: Optional[float] = None):
        e = BattleEventEnum.BTN_SWITCH_NORMAL_ATTACK.value
        log.info(e)
        self.ctx.controller.normal_attack(press_time)
        self.ctx.dispatch_event(e, time.time())

    def special_attack(self, press_time: Optional[float] = None):
        e = BattleEventEnum.BTN_SWITCH_SPECIAL_ATTACK.value
        log.info(e)
        self.ctx.controller.special_attack(press_time)
        self.ctx.dispatch_event(e, time.time())

    def init_context(self, agent_names: Optional[List[str]] = None) -> None:
        """
        重置上下文
        :return:
        """
        self.agent_list = []
        self.should_check_all_agents = True
        self.last_agent_diff_time = None

        for agent_name in agent_names:
            for agent_enum in AgentEnum:
                if agent_name == agent_enum.value.agent_name:
                    self.agent_list.append(agent_enum.value)
                    break

    def check_agent_related_async(self) -> None:
        """
        异步判断角色相关内容 并发送事件
        :return:
        """

        pass

    def check_agent_related(self) -> None:
        """
        判断角色相关内容 并发送事件
        :return:
        """
        pass

    def check_agent(self) -> None:
        """
        识别角色
        :return:
        """
        if self.should_check_all_agents:
            pass
        else:
            pass

    def _match_agent_in(self, img: MatLike, is_front: bool,
                        possible_agents: Optional[List[Agent]] = None) -> Optional[Agent]:
        """
        在候选列表重匹配角色 TODO 待优化
        :return:
        """
        if possible_agents is None:
            possible_agents = [enum.value for enum in AgentEnum]

        prefix = 'avatar_1_' if is_front else 'avatar_2_'
        for agent in possible_agents:
            mrl = self.ctx.tm.match_template(img, 'battle', prefix + agent.agent_id, threshold=0.9)
            if mrl.max is not None:
                return agent

        return None
