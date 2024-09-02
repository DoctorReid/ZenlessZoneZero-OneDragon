import time
from concurrent.futures import ThreadPoolExecutor, Future

import threading
from cv2.typing import MatLike
from enum import Enum
from typing import Optional, List, Union

from one_dragon.base.conditional_operation.state_event import StateEvent
from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.base.screen import screen_utils
from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.base.screen.screen_utils import FindAreaResultEnum
from one_dragon.utils import cv2_utils, debug_utils, thread_utils, cal_utils, str_utils
from one_dragon.utils.log_utils import log
from zzz_od.auto_battle.agent_state import agent_state_checker
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import Agent, AgentEnum, AgentStateCheckWay

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
    BTN_MOVE_W = '按键-移动-前'
    BTN_MOVE_S = '按键-移动-后'
    BTN_MOVE_A = '按键-移动-左'
    BTN_MOVE_D = '按键-移动-右'
    BTN_LOCK = '按键-锁定敌人'
    BTN_CHAIN_CANCEL = '按键-连携技-取消'

    STATUS_SPECIAL_READY = '按键可用-特殊攻击'
    STATUS_ULTIMATE_READY = '按键可用-终结技'
    STATUS_CHAIN_READY = '按键可用-连携技'
    STATUS_QUICK_ASSIST_READY = '按键可用-快速支援'


class AgentInfo:

    def __init__(self):
        self.agent: Optional[Agent] = None
        self.energy: float = 0  # 能量


class TeamInfo:

    def __init__(self):
        self.agent_list: List[AgentInfo] = []


class BattleContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx

        # 角色列表
        self.agent_list: List[Agent] = []
        self._allow_ultimate_list: Optional[List[dict[str, str]]] = None  # 允许使用终结技的角色
        self.should_check_all_agents: bool = True  # 是否应该检查所有角色
        self.check_agent_same_times: int = 0  # 识别角色的相同次数
        self.check_agent_diff_times: int = 0  # 识别角色的不同次数
        self._agent_update_time: float = 0  # 识别角色的更新时间
        self._to_check_states: Optional[set[str]] = None  # 需要识别的状态列表

        # 识别区域
        self._check_distance_area: Optional[ScreenArea] = None

        # 识别锁 保证每种类型只有1实例在进行识别
        self._update_agent_lock = threading.Lock()
        self._check_agent_lock = threading.Lock()
        self._check_special_attack_lock = threading.Lock()
        self._check_ultimate_lock = threading.Lock()
        self._check_chain_lock = threading.Lock()
        self._check_quick_lock = threading.Lock()
        self._check_end_lock = threading.Lock()
        self._check_distance_lock = threading.Lock()

        # 识别间隔
        self._check_agent_interval: Union[float, List[float]] = 0
        self._check_special_attack_interval: Union[float, List[float]] = 0
        self._check_ultimate_interval: Union[float, List[float]] = 0
        self._check_chain_interval: Union[float, List[float]] = 0
        self._check_quick_interval: Union[float, List[float]] = 0
        self._check_end_interval: Union[float, List[float]] = 5
        self._check_distance_interval: Union[float, List[float]] = 5

        # 上一次识别的时间
        self._last_check_agent_time: float = 0
        self._last_check_special_attack_time: float = 0
        self._last_check_ultimate_time: float = 0
        self._last_check_chain_time: float = 0
        self._last_check_quick_time: float = 0
        self._last_check_end_time: float = 0
        self._last_check_distance_time: float = 0

        # 识别结果
        self.last_check_end_result: Optional[str] = None
        self.last_check_distance: float = -1  # 最后一次识别的距离
        self.without_distance_times: int = 0  # 没有显示距离的次数
        self.with_distance_times: int = 0  # 有显示距离的次数

    def dodge(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            e = BattleEventEnum.BTN_DODGE.value + '-按下'
        elif release:
            e = BattleEventEnum.BTN_DODGE.value + '-松开'
        else:
            e = BattleEventEnum.BTN_DODGE.value

        self.ctx.controller.dodge(press=press, press_time=press_time, release=release)
        self.ctx.dispatch_event(e, StateEvent(time.time()))

    def switch_next(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        update_agent = False
        if press:
            e = BattleEventEnum.BTN_SWITCH_NEXT.value + '-按下'
            update_agent = True
        elif release:
            e = BattleEventEnum.BTN_SWITCH_NEXT.value + '-松开'
        else:
            e = BattleEventEnum.BTN_SWITCH_NEXT.value
            update_agent = True

        self.ctx.controller.switch_next(press=press, press_time=press_time, release=release)
        press_time = time.time()
        self.ctx.dispatch_event(e, StateEvent(press_time))
        if update_agent:
            self._agent_list_next(press_time)

    def switch_prev(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        update_agent = False
        if press:
            e = BattleEventEnum.BTN_SWITCH_PREV.value + '-按下'
            update_agent = True
        elif release:
            e = BattleEventEnum.BTN_SWITCH_PREV.value + '-松开'
        else:
            e = BattleEventEnum.BTN_SWITCH_PREV.value
            update_agent = True

        self.ctx.controller.switch_prev(press=press, press_time=press_time, release=release)
        press_time = time.time()
        self.ctx.dispatch_event(e, StateEvent(press_time))

        if update_agent:
            self._agent_list_prev(press_time)

    def normal_attack(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            e = BattleEventEnum.BTN_SWITCH_NORMAL_ATTACK.value + '-按下'
        elif release:
            e = BattleEventEnum.BTN_SWITCH_NORMAL_ATTACK.value + '-松开'
        else:
            e = BattleEventEnum.BTN_SWITCH_NORMAL_ATTACK.value

        self.ctx.controller.normal_attack(press=press, press_time=press_time, release=release)
        self.ctx.dispatch_event(e, StateEvent(time.time()))

    def special_attack(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            e = BattleEventEnum.BTN_SWITCH_SPECIAL_ATTACK.value + '-按下'
        elif release:
            e = BattleEventEnum.BTN_SWITCH_SPECIAL_ATTACK.value + '-松开'
        else:
            e = BattleEventEnum.BTN_SWITCH_SPECIAL_ATTACK.value

        self.ctx.controller.special_attack(press=press, press_time=press_time, release=release)
        self.ctx.dispatch_event(e, StateEvent(time.time()))

    def ultimate(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            e = BattleEventEnum.BTN_ULTIMATE.value + '-按下'
        elif release:
            e = BattleEventEnum.BTN_ULTIMATE.value + '-松开'
        else:
            e = BattleEventEnum.BTN_ULTIMATE.value

        self.ctx.controller.ultimate(press=press, press_time=press_time, release=release)
        self.ctx.dispatch_event(e, StateEvent(time.time()))

    def chain_left(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        update_agent = False
        if press:
            e = BattleEventEnum.BTN_CHAIN_LEFT.value + '-按下'
            update_agent = True
        elif release:
            e = BattleEventEnum.BTN_CHAIN_LEFT.value + '-松开'
        else:
            e = BattleEventEnum.BTN_CHAIN_LEFT.value
            update_agent = True

        self.ctx.controller.chain_left(press=press, press_time=press_time, release=release)
        press_time = time.time()
        self.ctx.dispatch_event(e, StateEvent(press_time))

        if update_agent:
            self._agent_list_prev(press_time)

    def chain_right(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        update_agent = False
        if press:
            e = BattleEventEnum.BTN_CHAIN_RIGHT.value + '-按下'
            update_agent = True
        elif release:
            e = BattleEventEnum.BTN_CHAIN_RIGHT.value + '-松开'
        else:
            e = BattleEventEnum.BTN_CHAIN_RIGHT.value
            update_agent = True

        self.ctx.controller.chain_right(press=press, press_time=press_time, release=release)
        press_time = time.time()
        self.ctx.dispatch_event(e, StateEvent(press_time))

        if update_agent:
            self._agent_list_next(press_time)

    def move_w(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            e = BattleEventEnum.BTN_MOVE_W.value + '-按下'
        elif release:
            e = BattleEventEnum.BTN_MOVE_W.value + '-松开'
        else:
            e = BattleEventEnum.BTN_MOVE_W.value

        self.ctx.controller.move_w(press=press, press_time=press_time, release=release)
        self.ctx.dispatch_event(e, StateEvent(time.time()))

    def move_s(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            e = BattleEventEnum.BTN_MOVE_S.value + '-按下'
        elif release:
            e = BattleEventEnum.BTN_MOVE_S.value + '-松开'
        else:
            e = BattleEventEnum.BTN_MOVE_S.value

        self.ctx.controller.move_s(press=press, press_time=press_time, release=release)
        self.ctx.dispatch_event(e, StateEvent(time.time()))

    def move_a(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            e = BattleEventEnum.BTN_MOVE_A.value + '-按下'
        elif release:
            e = BattleEventEnum.BTN_MOVE_A.value + '-松开'
        else:
            e = BattleEventEnum.BTN_MOVE_A.value

        self.ctx.controller.move_a(press=press, press_time=press_time, release=release)
        self.ctx.dispatch_event(e, StateEvent(time.time()))

    def move_d(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            e = BattleEventEnum.BTN_MOVE_D.value + '-按下'
        elif release:
            e = BattleEventEnum.BTN_MOVE_D.value + '-松开'
        else:
            e = BattleEventEnum.BTN_MOVE_D.value

        self.ctx.controller.move_d(press=press, press_time=press_time, release=release)
        self.ctx.dispatch_event(e, StateEvent(time.time()))

    def lock(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            e = BattleEventEnum.BTN_LOCK.value + '-按下'
        elif release:
            e = BattleEventEnum.BTN_LOCK.value + '-松开'
        else:
            e = BattleEventEnum.BTN_LOCK.value

        self.ctx.controller.lock(press=press, press_time=press_time, release=release)
        self.ctx.dispatch_event(e, StateEvent(time.time()))

    def chain_cancel(self, press: bool = False, press_time: Optional[float] = None, release: bool = False):
        if press:
            e = BattleEventEnum.BTN_CHAIN_CANCEL.value + '-按下'
        elif release:
            e = BattleEventEnum.BTN_CHAIN_CANCEL.value + '-松开'
        else:
            e = BattleEventEnum.BTN_CHAIN_CANCEL.value

        self.ctx.controller.chain_cancel(press=press, press_time=press_time, release=release)
        self.ctx.dispatch_event(e, StateEvent(time.time()))

    def init_context(self,
                     agent_names: Optional[List[str]] = None,
                     to_check_state_list: Optional[List[str]] = None,
                     allow_ultimate_list: Optional[List[dict[str, str]]] = None,
                     check_agent_interval: Union[float, List[float]] = 0,
                     check_special_attack_interval: Union[float, List[float]] = 0,
                     check_ultimate_interval: Union[float, List[float]] = 0,
                     check_chain_interval: Union[float, List[float]] = 0,
                     check_quick_interval: Union[float, List[float]] = 0,
                     check_end_interval: Union[float, List[float]] = 5,
                     ) -> None:
        """
        重置上下文
        :return:
        """
        self.agent_list = []
        self._to_check_states = set(to_check_state_list) if to_check_state_list is not None else None
        self._allow_ultimate_list = allow_ultimate_list
        self.should_check_all_agents = agent_names is None
        self.check_agent_same_times = 0
        self.check_agent_diff_times = 0

        if agent_names is not None:
            for agent_name in agent_names:
                for agent_enum in AgentEnum:
                    if agent_name == agent_enum.value.agent_name:
                        self.agent_list.append(agent_enum.value)
                        break

        # 识别区域 先读取出来 不要每次用的时候再读取
        self._check_distance_area = self.ctx.screen_loader.get_area('战斗画面', '距离显示区域')

        self.area_agent_3_1: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-3-1')
        self.area_agent_3_2: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-3-2')
        self.area_agent_3_3: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-3-3')
        self.area_agent_2_2: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '头像-2-2')

        self.area_btn_normal: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '按键-普通攻击')
        self.area_btn_special: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '按键-特殊攻击')
        self.area_btn_ultimate: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '按键-终结技')
        self.area_btn_switch: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '按键-切换角色')

        self.area_chain_1: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '连携技-1')
        self.area_chain_2: ScreenArea = self.ctx.screen_loader.get_area('战斗画面', '连携技-2')

        # 识别间隔
        self._check_agent_interval = check_agent_interval
        self._check_special_attack_interval = check_special_attack_interval
        self._check_ultimate_interval = check_ultimate_interval
        self._check_chain_interval = check_chain_interval
        self._check_quick_interval = check_quick_interval
        self._check_end_interval = check_end_interval
        self._check_distance_interval = 5

        # 上一次识别的时间
        self._last_check_agent_time: float = 0
        self._last_check_special_attack_time: float = 0
        self._last_check_ultimate_time: float = 0
        self._last_check_chain_time: float = 0
        self._last_check_quick_time: float = 0
        self._last_check_end_time: float = 0
        self._last_check_distance_time: float = 0

        # 识别结果
        self.last_check_end_result: Optional[str] = None
        self.without_distance_times: int = 0  # 没有显示距离的次数
        self.with_distance_times: int = 0  # 有显示距离的次数
        self.last_check_distance = -1

    def check_screen(self, screen: MatLike, screenshot_time: float,
                     check_battle_end_normal_result: bool = False,
                     check_battle_end_hollow_result: bool = False,
                     check_distance: bool = False,
                     sync: bool = False, in_battle: bool = True
                     ) -> None:
        """
        异步判断角战斗画面 并发送事件
        :return:
        """
        future_list: List[Future] = []

        if in_battle:
            future_list.append(_battle_check_executor.submit(self.check_agent_related, screen, screenshot_time))
            future_list.append(_battle_check_executor.submit(self.check_special_attack_btn, screen, screenshot_time))
            future_list.append(_battle_check_executor.submit(self.check_ultimate_btn, screen, screenshot_time))
            future_list.append(_battle_check_executor.submit(self.check_quick_assist, screen, screenshot_time))
            if check_distance:
                future_list.append(_battle_check_executor.submit(self._check_distance_with_lock, screen, screenshot_time))
        else:
            future_list.append(_battle_check_executor.submit(self.check_chain_attack, screen, screenshot_time))
            check_battle_end = check_battle_end_normal_result or check_battle_end_hollow_result
            if check_battle_end:
                future_list.append(_battle_check_executor.submit(
                    self._check_battle_end, screen, screenshot_time,
                    check_battle_end_normal_result, check_battle_end_hollow_result
                ))
        for future in future_list:
            future.add_done_callback(thread_utils.handle_future_result)

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
            if screenshot_time - self._last_check_agent_time < cal_utils.random_in_range(self._check_agent_interval):
                # 还没有达到识别间隔
                return
            self._last_check_agent_time = screenshot_time

            screen_agent_list = self._check_agent_in_parallel(screen, screenshot_time)
            self._check_front_agent_state(screen, screenshot_time, screen_agent_list)

        except Exception:
            log.error('识别画面角色失败', exc_info=True)
        finally:
            self._check_agent_lock.release()

    def _check_agent_in_parallel(self, screen: MatLike, screenshot_time: float) -> List[Agent]:
        """
        并发识别角色
        :return:
        """
        area_img = [
            cv2_utils.crop_image_only(screen, self.area_agent_3_1.rect),
            cv2_utils.crop_image_only(screen, self.area_agent_3_2.rect),
            cv2_utils.crop_image_only(screen, self.area_agent_3_3.rect),
            cv2_utils.crop_image_only(screen, self.area_agent_2_2.rect)
        ]

        possible_agents = self._get_possible_agent_list()

        result_agent_list: List[Optional[Agent]] = []
        future_list: List[Optional[Future]] = []
        should_check: List[bool] = [True, False, False, False]

        if not self.should_check_all_agents:
            if len(self.agent_list) == 3:
                should_check[1] = True
                should_check[2] = True
            elif len(self.agent_list) == 2:
                should_check[3] = True
        else:
            for i in range(4):
                should_check[i] = True

        for i in range(4):
            if should_check[i]:
                future_list.append(_battle_check_executor.submit(self._match_agent_in, area_img[i], i == 0, possible_agents))
            else:
                future_list.append(None)

        for future in future_list:
            if future is None:
                result_agent_list.append(None)
                continue
            try:
                result = future.result()
                result_agent_list.append(result)
            except Exception:
                log.error('识别角色头像失败', exc_info=True)
                result_agent_list.append(None)

        if result_agent_list[1] is not None and result_agent_list[2] is not None:  # 3人
            current_agent_list = result_agent_list[:3]
        elif result_agent_list[3] is not None:  # 2人
            current_agent_list = [result_agent_list[0], result_agent_list[3]]
        else:  # 1人
            current_agent_list = [result_agent_list[0]]

        if self.should_check_all_agents:
            if self._is_same_agent_list(current_agent_list):
                self.check_agent_same_times += 1
                if self.check_agent_same_times >= 5:  # 连续5次一致时 就不验证了
                    self.should_check_all_agents = False
                    log.debug("停止识别新角色")
            else:
                self.check_agent_same_times = 0
        else:
            if not self._is_same_agent_list(current_agent_list):
                self.check_agent_diff_times += 1
                if self.check_agent_diff_times >= 1000:  # 0.02秒1次 大概20s不一致就重新识别 基本不可能出现
                    self.should_check_all_agents = True
                    log.debug("重新识别新角色")
            else:
                self.check_agent_diff_times = 0

        self._update_agent_list(current_agent_list, screenshot_time)

        return current_agent_list

    def _match_agent_in(self, img: MatLike, is_front: bool,
                        possible_agents: Optional[List[Agent]] = None) -> Optional[Agent]:
        """
        在候选列表重匹配角色 TODO 待优化
        :return:
        """
        prefix = 'avatar_1_' if is_front else 'avatar_2_'
        for agent in possible_agents:
            mrl = self.ctx.tm.match_template(img, 'battle', prefix + agent.agent_id, threshold=0.8)
            if mrl.max is not None:
                return agent

        return None

    def _is_same_agent_list(self, current_agent_list: List[Agent]) -> bool:
        """
        是否跟原来的角色列表一致
        :param current_agent_list:
        :return:
        """
        if self.agent_list is None or current_agent_list is None:
            return False
        if len(self.agent_list) != len(current_agent_list):
            return False

        for agent in current_agent_list:
            if agent is None:
                return False
            if agent not in self.agent_list:
                return False
        return True

    def _agent_list_next(self, update_time: float) -> None:
        """
        代理人列表 切换下一个
        """
        if self.agent_list is None or len(self.agent_list) == 0:
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
        if self.agent_list is None or len(self.agent_list) == 0:
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
        with self._update_agent_lock:
            if update_time < self._agent_update_time:  # 可能是过时的截图 这时候不更新
                return
            any_none: bool = False
            for agent in current_agent_list:
                if agent is None:
                    any_none = True
            if not self.should_check_all_agents and not self._is_same_agent_list(current_agent_list):
                # 如果已经确定角色列表了 那识别出来的应该是一样的
                # 不一样的话 就不更新了
                pass
            elif not any_none:  # 需要都识别到才可以更新
                self.agent_list = current_agent_list

            log.debug('更新角色列表 %s', [
                agent.agent_name if agent is not None else 'none'
                for agent in current_agent_list
            ])

            log.debug('当前角色列表 %s', [
                agent.agent_name if agent is not None else 'none'
                for agent in self.agent_list
            ])

            for i in range(len(self.agent_list)):
                agent = self.agent_list[i]
                if agent is None:
                    continue
                prefix = '前台-' if i == 0 else ('后台-%d-' % i)
                self.ctx.dispatch_event(prefix + self.agent_list[i].agent_name, StateEvent(update_time))
                self.ctx.dispatch_event(prefix + self.agent_list[i].agent_type.value, StateEvent(update_time))

            if not self._allow_to_use_ultimate():  # 清除可用终结技的状态
                self.ctx.dispatch_event(BattleEventEnum.STATUS_ULTIMATE_READY.value, StateEvent(0), output_log=False)

    def check_special_attack_btn(self, screen: MatLike, screenshot_time: float) -> None:
        """
        识别特殊攻击按钮 看是否可用
        """
        if not self._check_special_attack_lock.acquire(blocking=False):
            return
        try:
            if screenshot_time - self._last_check_special_attack_time < cal_utils.random_in_range(self._check_special_attack_interval):
                # 还没有达到识别间隔
                return
            self._last_check_special_attack_time = screenshot_time

            part = cv2_utils.crop_image_only(screen, self.area_btn_special.rect)
            mrl = self.ctx.tm.match_template(part, 'battle', 'btn_special_attack_2',
                                             threshold=0.9)
            is_ready = mrl.max is not None
            self.ctx.dispatch_event(BattleEventEnum.STATUS_SPECIAL_READY.value,
                                    StateEvent(screenshot_time if is_ready else 0),
                                    output_log=is_ready)
        except Exception:
            log.error('识别特殊攻击按键出错', exc_info=True)
        finally:
            self._check_special_attack_lock.release()

    def check_ultimate_btn(self, screen: MatLike, screenshot_time: float) -> None:
        """
        识别终结技按钮 看是否可用
        """
        if not self._check_ultimate_lock.acquire(blocking=False):
            return

        try:
            if not self._allow_to_use_ultimate():
                return

            if screenshot_time - self._last_check_ultimate_time < cal_utils.random_in_range(self._check_ultimate_interval):
                # 还没有达到识别间隔
                return
            self._last_check_ultimate_time = screenshot_time

            part = cv2_utils.crop_image_only(screen, self.area_btn_ultimate.rect)
            # 判断灰色按钮比较容易 发光时颜色会变
            mrl = self.ctx.tm.match_template(part, 'battle', 'btn_ultimate_2',
                                             threshold=0.9)
            is_ready = mrl.max is not None
            # cv2_utils.show_image(part, win_name='part', wait=0)
            self.ctx.dispatch_event(BattleEventEnum.STATUS_ULTIMATE_READY.value,
                                    StateEvent(screenshot_time if is_ready else 0),
                                    output_log=is_ready)
        except Exception:
            log.error('识别终结技按键出错', exc_info=True)
        finally:
            self._check_ultimate_lock.release()

    def _allow_to_use_ultimate(self) -> bool:
        """
        当前角色是否允许使用终结技
        :return:
        """
        if self._allow_ultimate_list is not None:  # 如果配置了终结技
            if len(self.agent_list) == 0 or self.agent_list[0] is None:  # 未识别到角色时 不允许使用
                return False

            for allow_ultimate_item in self._allow_ultimate_list:
                if 'agent_name' in allow_ultimate_item:
                    if allow_ultimate_item.get('agent_name', '') == self.agent_list[0].agent_name:
                        return True
                elif 'agent_type' in allow_ultimate_item:
                    if allow_ultimate_item.get('agent_type', '') == self.agent_list[0].agent_type.value:
                        return True

            return False

        return True

    def check_chain_attack(self, screen: MatLike, screenshot_time: float) -> None:
        """
        识别连携技
        """
        if not self._check_chain_lock.acquire(blocking=False):
            return

        try:
            if screenshot_time - self._last_check_chain_time < cal_utils.random_in_range(self._check_chain_interval):
                # 还没有达到识别间隔
                return
            self._last_check_chain_time = screenshot_time

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
            self.ctx.dispatch_event(f'连携技-{i + 1}-{result_agent_list[i].agent_name}', StateEvent(screenshot_time))
            self.ctx.dispatch_event(f'连携技-{i + 1}-{result_agent_list[i].agent_type.value}', StateEvent(screenshot_time))
            chain = True

        if chain:
            self.ctx.dispatch_event(BattleEventEnum.STATUS_CHAIN_READY.value, StateEvent(screenshot_time))

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
            if screenshot_time - self._last_check_quick_time < cal_utils.random_in_range(self._check_quick_interval):
                # 还没有达到识别间隔
                return
            self._last_check_quick_time = screenshot_time

            part = cv2_utils.crop_image_only(screen, self.area_btn_switch.rect)

            possible_agents = self._get_possible_agent_list()

            agent = self._match_quick_assist_agent_in(part, possible_agents)

            if agent is not None:
                self.ctx.dispatch_event(f'快速支援-{agent.agent_name}', StateEvent(screenshot_time))
                self.ctx.dispatch_event(f'快速支援-{agent.agent_type.value}', StateEvent(screenshot_time))
                self.ctx.dispatch_event(BattleEventEnum.STATUS_QUICK_ASSIST_READY.value, StateEvent(screenshot_time))
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

    def _check_battle_end(self, screen: MatLike, screenshot_time: float,
                          check_battle_end_normal_result: bool,
                          check_battle_end_hollow_result: bool) -> None:
        if not self._check_end_lock.acquire(blocking=False):
            return

        try:
            if screenshot_time - self._last_check_end_time < cal_utils.random_in_range(self._check_end_interval):
                # 还没有达到识别间隔
                return
            self._last_check_end_time = screenshot_time

            agent = self._check_agent_1(screen)
            if agent is not None:  # 有显示角色 就一定没有结束
                self.last_check_end_result = None
                return

            if check_battle_end_hollow_result:
                result = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                                screen_name='零号空洞-战斗', area_name='挑战结果')
                if result == FindAreaResultEnum.TRUE:
                    self.last_check_end_result = '零号空洞-挑战结果'
                    return

                result = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                                screen_name='零号空洞-事件', area_name='背包')
                if result == FindAreaResultEnum.TRUE:
                    self.last_check_end_result = '零号空洞-背包'
                    return

                result = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                                screen_name='零号空洞-战斗', area_name='鸣徽-确定')
                if result == FindAreaResultEnum.TRUE:
                    self.last_check_end_result = '鸣徽-确定'
                    return

            if check_battle_end_normal_result:
                result = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                                screen_name='战斗画面', area_name='战斗结果-完成')
                if result == FindAreaResultEnum.TRUE:
                    self.last_check_end_result = '普通战斗-完成'
                    return
                result = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                                screen_name='战斗画面', area_name='战斗结果-撤退')
                if result == FindAreaResultEnum.TRUE:
                    self.last_check_end_result = '普通战斗-撤退'
                    return

            self.last_check_end_result = None
        except Exception:
            log.error('识别战斗结束失败', exc_info=True)
        finally:
            self._check_end_lock.release()

    def _check_distance_with_lock(self, screen: MatLike, screenshot_time: float) -> None:
        if not self._check_distance_lock.acquire(blocking=False):
            return

        try:
            if screenshot_time - self._last_check_distance_time < cal_utils.random_in_range(self._check_distance_interval):
                # 还没有达到识别间隔
                return

            self._last_check_distance_time = screenshot_time

            agent = self._check_agent_1(screen)
            if agent is None:  # 没有显示角色 就一定没有距离
                self.without_distance_times += 1
                self.with_distance_times = 0
                self.last_check_distance = -1
                self._check_distance_interval = 5
                return

            self.check_battle_distance(screen)
        except Exception:
            log.error('识别距离失败', exc_info=True)
        finally:
            self._check_distance_lock.release()

    def check_battle_distance(self, screen: MatLike) -> MatchResult:
        """
        识别画面上显示的距离
        :param screen:
        :return:
        """
        area = self._check_distance_area
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part)

        distance: Optional[float] = None
        mr: Optional[MatchResult] = None
        for ocr_result, mrl in ocr_result_map.items():
            if not ocr_result.endswith('m'):
                continue
            pre_str = ocr_result[:-1]
            distance = str_utils.get_positive_float(pre_str, None)
            if distance is None:
                continue
            mr = mrl.max

        if mr is not None:
            mr.add_offset(area.left_top)
            mr.data = distance
            self.without_distance_times = 0
            self.with_distance_times += 1
            self.last_check_distance = distance
            self._check_distance_interval = 1  # 识别到距离的话 减少识别间隔
        else:
            self.without_distance_times += 1
            self.with_distance_times = 0
            self.last_check_distance = -1
            self._check_distance_interval = 5

        return mr

    def _check_agent_1(self, screen: MatLike) -> Optional[Agent]:
        """
        识别第一个角色
        :return:
        """
        img = cv2_utils.crop_image_only(screen, self.area_agent_3_1.rect)
        return self._match_agent_in(img, True, self._get_possible_agent_list())

    def is_normal_attack_btn_available(self, screen: MatLike) -> bool:
        """
        识别普通攻击按钮是否存在 用了粗略判断是否在战斗画面 2~3ms
        :param screen:
        :return:
        """
        part = cv2_utils.crop_image_only(screen, self.area_btn_normal.rect)
        mrl = self.ctx.tm.match_template(part, 'battle', 'btn_normal_attack',
                                         threshold=0.9)
        return mrl.max is not None

    def _check_front_agent_state(self, screen: MatLike, screenshot_time: float, screen_agent_list: List[Agent]) -> None:
        """
        识别前台角色的状态
        :param screen: 游戏画面
        :param screenshot_time: 截图时间
        :param screen_agent_list: 当前画面前台角色
        :return:
        """
        if screen_agent_list is None or len(screen_agent_list) == 0 or screen_agent_list[0] is None:
            return
        front_agent: Agent = screen_agent_list[0]
        if front_agent.state_list is None:
            return

        for state in front_agent.state_list:
            if self._to_check_states is not None and state.state_name not in self._to_check_states:
                continue
            if state.check_way == AgentStateCheckWay.COLOR_RANGE_CONNECT:
                value = agent_state_checker.check_cnt_by_color_range(self.ctx, screen, state)
                self.ctx.dispatch_event(state.state_name, StateEvent(screenshot_time, value=value))
            elif state.check_way == AgentStateCheckWay.BACKGROUND_COLOR_RANGE_LENGTH:
                value = agent_state_checker.check_length_by_background(self.ctx, screen, state)
                self.ctx.dispatch_event(state.state_name, StateEvent(screenshot_time, value=value))


def __debug():
    ctx = ZContext()
    battle = BattleContext(ctx)
    battle.init_context()
    screen = debug_utils.get_debug_image('_1724044474644')
    # battle.check_agent(screen, 0)
    # battle.check_special_attack_btn(screen, 0)
    # battle.check_ultimate_btn(screen, 0)
    # battle.check_chain_attack(screen, 0)
    # battle.check_quick_assist(screen, 0)
    battle.is_normal_attack_btn_available(screen)
    t1 = time.time()
    battle.is_normal_attack_btn_available(screen)
    print(time.time() - t1)


if __name__ == '__main__':
    __debug()