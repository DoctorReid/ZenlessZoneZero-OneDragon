import time
from concurrent.futures import ThreadPoolExecutor, Future

import threading
from cv2.typing import MatLike
from enum import Enum
from typing import Optional, List

from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.utils import cv2_utils, debug_utils
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
    BTN_ULTIMATE = '按键-终结技'
    BTN_CHAIN_LEFT = '按键-连携技-左'
    BTN_CHAIN_RIGHT = '按键-连携技-右'

    STATUS_SPECIAL_READY = '按键可用-特殊攻击'
    STATUS_ULTIMATE_READY = '按键可用-终结技'
    STATUS_CHAIN_READY = '按键可用-连携技'
    STATUS_QUICK_ASSIST_READY = '按键可用-快速支援'


class BattleContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx

        # 角色列表
        self.agent_list: List[Agent] = []
        self.should_check_all_agents: bool = True  # 是否应该检查所有角色
        self.check_agent_same_times: int = 0  # 识别角色的相同次数
        self.check_agent_diff_times: int = 0  # 识别角色的不同次数

        # 识别锁 保证每种类型只有1实例在进行识别
        self._check_agent_lock = threading.Lock()
        self._check_special_attack_lock = threading.Lock()
        self._check_ultimate_lock = threading.Lock()
        self._check_chain_lock = threading.Lock()
        self._check_quick_lock = threading.Lock()

    def dodge(self):
        e = BattleEventEnum.BTN_DODGE.value
        log.info(e)
        self.ctx.controller.dodge()
        self.ctx.dispatch_event(e, time.time())

    def switch_next(self):
        e = BattleEventEnum.BTN_SWITCH_NEXT.value
        log.info(e)
        self.ctx.controller.switch_next()
        press_time = time.time()
        self.ctx.dispatch_event(e, press_time)

        self._agent_list_next(press_time)

    def switch_prev(self):
        e = BattleEventEnum.BTN_SWITCH_PREV.value
        log.info(e)
        self.ctx.controller.switch_prev()
        press_time = time.time()
        self.ctx.dispatch_event(e, press_time)

        self._agent_list_prev(press_time)

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

    def ultimate(self):
        e = BattleEventEnum.BTN_ULTIMATE.value
        log.info(e)
        self.ctx.controller.ultimate()
        self.ctx.dispatch_event(e, time.time())

    def chain_left(self):
        e = BattleEventEnum.BTN_CHAIN_LEFT.value
        log.info(e)
        self.ctx.controller.chain_left()
        press_time = time.time()
        self.ctx.dispatch_event(e, press_time)

        self._agent_list_prev(press_time)

    def chain_right(self):
        e = BattleEventEnum.BTN_CHAIN_RIGHT.value
        log.info(e)
        self.ctx.controller.chain_right()
        press_time = time.time()
        self.ctx.dispatch_event(e, press_time)

        self._agent_list_next(press_time)

    def init_context(self, agent_names: Optional[List[str]] = None) -> None:
        """
        重置上下文
        :return:
        """
        self.agent_list = []
        self.should_check_all_agents = agent_names is None
        self.check_agent_same_times = 0

        if agent_names is not None:
            for agent_name in agent_names:
                for agent_enum in AgentEnum:
                    if agent_name == agent_enum.value.agent_name:
                        self.agent_list.append(agent_enum.value)
                        break

        # 画面区域 先读取出来 不要每次用的时候再读取
        self.area_agent_3_1: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-3-1')
        self.area_agent_3_2: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-3-2')
        self.area_agent_3_3: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-3-3')
        self.area_agent_2_2: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-2-2')

        self.area_btn_special: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '按键-特殊攻击')
        self.area_btn_ultimate: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '按键-终结技')
        self.area_btn_switch: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '按键-切换角色')

        self.area_chain_1: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '连携技-1')
        self.area_chain_2: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '连携技-2')

    def check_screen(self, screen: MatLike, screenshot_time: float,
                     allow_ultimate_list: Optional[List[dict[str, str]]] = None,
                     sync: bool = False) -> None:
        """o
        异步判断角战斗画面 并发送世界
        :return:
        """
        future_list: List[Future] = []

        future_list.append(_battle_check_executor.submit(self.check_agent_related, screen, screenshot_time))
        future_list.append(_battle_check_executor.submit(self.check_special_attack_btn, screen, screenshot_time))
        future_list.append(_battle_check_executor.submit(self.check_ultimate_btn, screen, screenshot_time, allow_ultimate_list))
        future_list.append(_battle_check_executor.submit(self.check_chain_attack, screen, screenshot_time))
        future_list.append(_battle_check_executor.submit(self.check_quick_assist, screen, screenshot_time))

        if sync:
            for future in future_list:
                future.result()

    def check_agent_related(self, screen: MatLike, screenshot_time: float) -> None:
        """
        判断角色相关内容 并发送事件
        :return:
        """
        if not self._check_agent_lock.acquire(blocking=False):
            return

        try:
            self._check_agent_in_parallel(screen, screenshot_time)
        except Exception:
            log.error('识别画面角色失败', exc_info=True)
        finally:
            self._check_agent_lock.release()

    def _check_agent_in_parallel(self, screen: MatLike, screenshot_time: float) -> None:
        """
        并发识别角色
        :return:
        """
        a31: MatLike = cv2_utils.crop_image_only(screen, self.area_agent_3_1.rect)
        a32: MatLike = cv2_utils.crop_image_only(screen, self.area_agent_3_2.rect)
        a33: MatLike = cv2_utils.crop_image_only(screen, self.area_agent_3_3.rect)
        a22: MatLike = cv2_utils.crop_image_only(screen, self.area_agent_2_2.rect)

        possible_agents = self._get_possible_agent_list()

        result_agent_list: List[Agent] = []
        future_list: List[Future] = []
        future_list.append(_battle_check_executor.submit(self._match_agent_in, a31, True, possible_agents))
        future_list.append(_battle_check_executor.submit(self._match_agent_in, a32, False, possible_agents))
        future_list.append(_battle_check_executor.submit(self._match_agent_in, a33, False, possible_agents))
        future_list.append(_battle_check_executor.submit(self._match_agent_in, a22, False, possible_agents))

        for future in future_list:
            try:
                result = future.result()
                result_agent_list.append(result)
            except Exception:
                log.error('识别角色头像失败', exc_info=True)
                result_agent_list.append(None)

        if result_agent_list[1] is not None and result_agent_list[2] is not None:  # 3人
            result_agent_list.pop(-1)
        elif result_agent_list[3] is not None:  # 2人
            result_agent_list.pop(1)
            result_agent_list.pop(1)
        else:  # 1人
            result_agent_list = [result_agent_list[0]]

        if self.should_check_all_agents:
            if self._is_same_agent_list(result_agent_list):
                self.check_agent_same_times += 1
                if self.check_agent_same_times >= 5:  # 连续5次一致时 就不验证了
                    self.should_check_all_agents = False
            else:
                self.check_agent_same_times = 0
        else:
            if not self._is_same_agent_list(result_agent_list):
                self.check_agent_diff_times += 1
                if self.check_agent_diff_times >= 1000:  # 0.02秒1次 大概20s不一致就重新识别 基本不可能出现
                    self.should_check_all_agents = True
            else:
                self.check_agent_diff_times = 0

        self._update_agent_list(result_agent_list, screenshot_time)

    def _match_agent_in(self, img: MatLike, is_front: bool,
                        possible_agents: Optional[List[Agent]] = None) -> Optional[Agent]:
        """
        在候选列表重匹配角色 TODO 待优化
        :return:
        """
        prefix = 'avatar_1_' if is_front else 'avatar_2_'
        for agent in possible_agents:
            mrl = self.ctx.tm.match_template(img, 'battle', prefix + agent.agent_id, threshold=0.9)
            if mrl.max is not None:
                return agent

        return None

    def _is_same_agent_list(self, current_agent_list: List[Agent]) -> bool:
        """
        是否跟原来的角色列表一致
        :param current_agent_list:
        :return:
        """
        for agent in current_agent_list:
            if agent not in self.agent_list:
                return False
        return True

    def _agent_list_next(self, update_time: float) -> None:
        """
        代理人列表 切换下一个
        """
        if self.agent_list is None:
            return
        current_agent_list = self.agent_list
        next_agent_list = []
        for i in range(1, len(current_agent_list)):
            next_agent_list.append(current_agent_list[i])
        next_agent_list.append(current_agent_list[0])
        self._update_agent_list(next_agent_list, update_time)

    def _agent_list_prev(self, update_time: float) -> None:
        """
        代理人列表 切换上一个
        """
        if self.agent_list is None:
            return
        current_agent_list = self.agent_list
        next_agent_list = []
        next_agent_list.append(current_agent_list[-1])
        for i in range(0, len(current_agent_list)-1):
            next_agent_list.append(current_agent_list[i])
        self._update_agent_list(next_agent_list, update_time)

    def _update_agent_list(self, current_agent_list: List[Agent], update_time: float) -> None:
        """
        更新角色列表
        :param current_agent_list: 新的角色列表
        :return:
        """
        if not self.should_check_all_agents and not self._is_same_agent_list(current_agent_list):
            # 如果已经确定角色列表了 那识别出来的应该是一样的
            # 不一样的话 就不更新了
            pass
        else:
            self.agent_list = current_agent_list

        log.debug('当前角色列表 %s', [
            agent.agent_name if agent is not None else 'none'
            for agent in self.agent_list
        ])

        for i in range(len(self.agent_list)):
            agent = self.agent_list[i]
            if agent is None:
                continue
            prefix = '前台-' if i == 0 else '后台-'
            self.ctx.dispatch_event(prefix + self.agent_list[i].agent_name, update_time)
            self.ctx.dispatch_event(prefix + self.agent_list[i].agent_type.value, update_time)

    def check_special_attack_btn(self, screen: MatLike, screenshot_time: float) -> None:
        """
        识别特殊攻击按钮 看是否可用
        """
        if not self._check_special_attack_lock.acquire(blocking=False):
            return
        try:
            part = cv2_utils.crop_image_only(screen, self.area_btn_special.rect)
            # 判断灰色按钮比较容易
            mrl = self.ctx.tm.match_template(part, 'battle', 'btn_special_attack_1',
                                             threshold=0.9)
            is_ready = mrl.max is None
            self.ctx.dispatch_event(BattleEventEnum.STATUS_SPECIAL_READY.value,
                                    screenshot_time if is_ready else 0,
                                    output_log=is_ready)
        except Exception:
            log.error('识别特殊攻击按键出错', exc_info=True)
        finally:
            self._check_special_attack_lock.release()

    def check_ultimate_btn(self, screen: MatLike, screenshot_time: float,
                           allow_ultimate_list: Optional[List[dict[str, str]]] = None) -> None:
        """
        识别终结技按钮 看是否可用
        """
        if not self._check_ultimate_lock.acquire(blocking=False):
            return

        try:
            if allow_ultimate_list is not None:  # 如何配置了终结技
                if len(self.agent_list) == 0 or self.agent_list[0] is None:  # 未识别到角色时 不允许使用
                    return None

                allow: bool = False
                for allow_ultimate_item in allow_ultimate_list:
                    if 'agent_name' in allow_ultimate_item:
                        if allow_ultimate_item.get('agent_name', '') == self.agent_list[0].agent_name:
                            allow = True
                            break
                    elif 'agent_type' in allow_ultimate_item:
                        if allow_ultimate_item.get('agent_type', '') == self.agent_list[0].agent_type.value:
                            allow = True
                            break

                if not allow:  # 当前角色不允许使用终结技
                    return

            part = cv2_utils.crop_image_only(screen, self.area_btn_ultimate.rect)
            # 判断灰色按钮比较容易 发光时颜色会变
            mrl = self.ctx.tm.match_template(part, 'battle', 'btn_ultimate_1',
                                             threshold=0.9)
            is_ready = mrl.max is None
            # cv2_utils.show_image(part, win_name='part', wait=0)
            self.ctx.dispatch_event(BattleEventEnum.STATUS_ULTIMATE_READY.value,
                                    screenshot_time if is_ready else 0,
                                    output_log=is_ready)
        except Exception:
            log.error('识别终结技按键出错', exc_info=True)
        finally:
            self._check_ultimate_lock.release()

    def check_chain_attack(self, screen: MatLike, screenshot_time: float) -> None:
        """
        识别连携技
        """
        if not self._check_chain_lock.acquire(blocking=False):
            return

        try:
            self._check_chain_attack_in_parallel(screen, screenshot_time)
        except Exception:
            log.error('识别连携技出错', exc_info=True)
        finally:
            self._check_chain_lock.release()

    def _check_chain_attack_in_parallel(self, screen: MatLike, screenshot_time: float):
        """
        并行识别连携技角色
        """
        c1 = cv2_utils.crop_image_only(screen, self.area_chain_1.rect)
        c2 = cv2_utils.crop_image_only(screen, self.area_chain_2.rect)

        possible_agents = self._get_possible_agent_list()

        result_agent_list: List[Agent] = []
        future_list: List[Future] = []
        future_list.append(_battle_check_executor.submit(self._match_chain_agent_in, c1, possible_agents))
        future_list.append(_battle_check_executor.submit(self._match_chain_agent_in, c2, possible_agents))

        for future in future_list:
            try:
                result = future.result()
                result_agent_list.append(result)
            except Exception:
                log.error('识别连携技角色头像失败', exc_info=True)
                result_agent_list.append(None)

        chain: bool = False  # 是否有连携技
        for i in range(len(result_agent_list)):
            if result_agent_list[i] is None:
                continue
            self.ctx.dispatch_event(f'连携技-{i + 1}-{result_agent_list[i].agent_name}', screenshot_time)
            self.ctx.dispatch_event(f'连携技-{i + 1}-{result_agent_list[i].agent_type.value}', screenshot_time)
            chain = True

        if chain:
            self.ctx.dispatch_event(BattleEventEnum.STATUS_CHAIN_READY.value, screenshot_time)

    def _match_chain_agent_in(self, img: MatLike, possible_agents: Optional[List[Agent]] = None) -> Optional[Agent]:
        """
        在候选列表重匹配角色 TODO 待优化
        :return:
        """
        for agent in possible_agents:
            mrl = self.ctx.tm.match_template(img, 'battle', 'avatar_chain_' + agent.agent_id, threshold=0.8)
            if mrl.max is not None:
                return agent

        return None

    def check_quick_assist(self, screen: MatLike, screenshot_time: float) -> None:
        """
        识别快速支援
        """
        if not self._check_quick_lock.acquire(blocking=False):
            return

        try:
            part = cv2_utils.crop_image_only(screen, self.area_btn_switch.rect)

            possible_agents = self._get_possible_agent_list()

            agent = self._match_quick_assist_agent_in(part, possible_agents)

            if agent is not None:
                self.ctx.dispatch_event(f'快速支援-{agent.agent_name}', screenshot_time)
                self.ctx.dispatch_event(f'快速支援-{agent.agent_type.value}', screenshot_time)
                self.ctx.dispatch_event(BattleEventEnum.STATUS_QUICK_ASSIST_READY.value, screenshot_time)
        except Exception:
            log.error('识别快速支援失败', exc_info=True)
        finally:
            self._check_quick_lock.release()

    def _match_quick_assist_agent_in(self, img: MatLike, possible_agents: Optional[List[Agent]] = None) -> Optional[Agent]:
        """
        在候选列表重匹配角色 TODO 待优化
        :return:
        """
        for agent in possible_agents:
            mrl = self.ctx.tm.match_template(img, 'battle', 'avatar_quick_' + agent.agent_id, threshold=0.9)
            if mrl.max is not None:
                return agent

        return None

    def _get_possible_agent_list(self) -> Optional[List[Agent]]:
        """
        获取用于匹配的候选角色列表
        """
        all: bool = False
        if self.should_check_all_agents:
            all = True
        elif self.agent_list is None or len(self.agent_list) == 0:
            all = True
        else:
            for agent in self.agent_list:
                if agent is None:
                    all = True
                    break
        if all:
            return [agent_enum.value for agent_enum in AgentEnum]
        else:
            return self.agent_list

def __debug():
    ctx = ZContext()
    battle = BattleContext(ctx)
    battle.init_context()
    screen = debug_utils.get_debug_image('_1722146684408')
    # battle.check_agent(screen, 0)
    # battle.check_special_attack_btn(screen, 0)
    # battle.check_ultimate_btn(screen, 0)
    # battle.check_chain_attack(screen, 0)
    battle.check_quick_assist(screen, 0)


if __name__ == '__main__':
    __debug()