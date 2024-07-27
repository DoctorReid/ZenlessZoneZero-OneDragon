import time
from concurrent.futures import ThreadPoolExecutor, Future

from cv2.typing import MatLike
from enum import Enum
from typing import Optional, List

from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.utils import cv2_utils
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

    STATUS_SPECIAL_READY = '按键可用-特殊攻击'
    STATUS_ULTIMATE_READY = '按键可用-终结技'


class BattleContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx

        # 角色列表
        self.agent_list: List[Agent] = []
        self.should_check_all_agents: bool = True  # 是否应该检查所有角色
        self.check_agent_same_times: int = 0  # 识别角色的相同次数

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
        self.should_check_all_agents = agent_names is None
        self.check_agent_same_times = 0

        for agent_name in agent_names:
            for agent_enum in AgentEnum:
                if agent_name == agent_enum.value.agent_name:
                    self.agent_list.append(agent_enum.value)
                    break

        self.area_agent_3_1: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-3-1')
        self.area_agent_3_2: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-3-2')
        self.area_agent_3_3: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-3-3')
        self.area_agent_2_2: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-2-2')

        self.area_btn_special: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '按键-特殊攻击')
        self.area_btn_ultimate: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '按键-终结技')

    def check_battle_screen(self, screen: MatLike, screenshot_time: float) -> None:
        """
        异步判断角战斗画面 并发送世界
        :return:
        """
        _battle_check_executor.submit(self.check_agent_related, screen, screenshot_time)
        _battle_check_executor.submit(self.check_special_attack_btn, screen, screenshot_time)

    def check_agent_related(self, screen: MatLike, screenshot_time: float) -> None:
        """
        判断角色相关内容 并发送事件
        :return:
        """
        self.check_agent(screen, screenshot_time)

    def check_agent(self, screen: MatLike, screenshot_time: float) -> None:
        """
        识别角色
        :return:
        """
        a31: MatLike = cv2_utils.crop_image_only(screen, self.area_agent_3_1.rect)
        a32: MatLike = cv2_utils.crop_image_only(screen, self.area_agent_3_2.rect)
        a33: MatLike = cv2_utils.crop_image_only(screen, self.area_agent_3_3.rect)
        a22: MatLike = cv2_utils.crop_image_only(screen, self.area_agent_2_2.rect)

        if self.should_check_all_agents:
            possible_agents = None
        else:
            possible_agents = self.agent_list

        result_agent_list: List[Agent] = []
        future_list: List[Future] = []
        if possible_agents is None:
            future_list.append(_battle_check_executor.submit(self._match_agent_in, a31, True, None))
            future_list.append(_battle_check_executor.submit(self._match_agent_in, a32, False, None))
            future_list.append(_battle_check_executor.submit(self._match_agent_in, a33, False, None))
            future_list.append(_battle_check_executor.submit(self._match_agent_in, a22, False, None))

        for future in future_list:
            result_agent_list.append(future.result())

        if result_agent_list[1] is not None and result_agent_list[2] is not None:  # 3人
            result_agent_list.pop(-1)
        elif result_agent_list[3] is not None:  # 2人
            result_agent_list.pop(1)
            result_agent_list.pop(1)
        else:  # 1人
            result_agent_list = [result_agent_list[0]]

        if self.should_check_all_agents:
            if self.is_same_agent_list(result_agent_list):
                self.check_agent_same_times += 1
                if self.check_agent_same_times >= 5:  # 连续5次一致时 就不验证了
                    self.should_check_all_agents = False
            else:
                self.check_agent_same_times = 0

        self.agent_list = result_agent_list
        for i in range(len(self.agent_list)):
            prefix = '前台-' if i == 0 else '后台-'
            self.ctx.dispatch_event(prefix + self.agent_list[i].agent_name, screenshot_time)
            self.ctx.dispatch_event(prefix + self.agent_list[i].agent_type.value)

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

    def is_same_agent_list(self, current_agent_list: List[Agent]) -> bool:
        """
        是否跟原来的角色列表一致
        :param current_agent_list:
        :return:
        """
        for agent in current_agent_list:
            if agent not in self.agent_list:
                return False
        return True

    def check_special_attack_btn(self, screen: MatLike, screenshot_time: float) -> None:
        """
        识别特殊攻击按钮 看是否可用
        """
        part = cv2_utils.crop_image_only(screen, self.area_btn_special.rect)
        mrl = self.ctx.tm.match_template(part, 'battle', 'btn_special_attack_2',
                                         threshold=0.9)
        self.ctx.dispatch_event(BattleEventEnum.STATUS_SPECIAL_READY.value, screenshot_time if mrl is not None else 0)

    def check_ultimate_btn(self, screen: MatLike, screenshot_time: float) -> None:
        """
        识别终结技按钮 看是否可用
        """
        part = cv2_utils.crop_image_only(screen, self.area_btn_special.rect)
        mrl = self.ctx.tm.match_template(part, 'battle', 'btn_ultimate_2',
                                         threshold=0.9)
        self.ctx.dispatch_event(BattleEventEnum.STATUS_ULTIMATE_READY.value, screenshot_time if mrl is not None else 0)
