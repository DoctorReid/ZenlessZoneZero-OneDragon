from concurrent.futures import ThreadPoolExecutor, Future

import threading
from cv2.typing import MatLike
from typing import List, Optional, Union

from one_dragon.base.screen import screen_utils
from one_dragon.base.screen.screen_utils import FindAreaResultEnum
from one_dragon.utils import cv2_utils, thread_utils, cal_utils
from one_dragon.utils.log_utils import log
from zzz_od.context.hollow_level_info import HollowLevelInfo
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import Agent, AgentEnum
from zzz_od.operation.hollow_zero.hollow_zero_event import HallowZeroEventService

_hollow_context_executor = ThreadPoolExecutor(thread_name_prefix='od_hollow_context', max_workers=16)


class HollowContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx
        self.agent_list: List[Agent]

        self.event_service: HallowZeroEventService = HallowZeroEventService()
        self.level_info: HollowLevelInfo = HollowLevelInfo()

        # 识别锁 保证每种类型只有1实例在进行识别
        self._check_end_lock = threading.Lock()

        # 识别间隔
        self._check_end_interval: Union[float, List[float]] = 5

        # 上一次识别的时间
        self._last_check_end_time: float = 0

        # 上一次识别的结果
        self._last_check_end_result: bool = False

    def init_context(self,
                     check_end_interval: Union[float, List[float]] = 5,):
        # 识别间隔
        self._check_end_interval = check_end_interval

        # 上一次识别的时间
        self._last_check_end_time = 0

        # 上一次识别的结果
        self._last_check_end_result = False

    def check_agent_list(self, screen: MatLike) -> Optional[List[Agent]]:
        """
        识别空洞画面里的角色列表
        """
        area = [
            self.ctx.screen_loader.get_area('零号空洞-事件', ('角色-%d' % i))
            for i in range(1, 4)
        ]
        area_img = [
            cv2_utils.crop_image_only(screen, i.rect)
            for i in area
        ]

        result_agent_list: List[Optional[Agent]] = []
        future_list: List[Future] = []

        for img in area_img:
            future_list.append(_hollow_context_executor.submit(self._match_agent_in, img, None))

        any_not_none: bool = False
        for future in future_list:
            try:
                result = future.result()
                result_agent_list.append(result)
                if result is not None:
                    any_not_none = True
            except Exception:
                log.error('识别角色头像失败', exc_info=True)
                result_agent_list.append(None)

        if not any_not_none:
            return None
        self.agent_list = result_agent_list
        return self.agent_list

    def _match_agent_in(self, img: MatLike, possible_agents: Optional[List[Agent]] = None) -> Optional[Agent]:
        """
        在候选列表重匹配角色 TODO 待优化
        :return:
        """
        prefix = 'avatar_'
        if possible_agents is None:
            possible_agents = [agent_enum.value for agent_enum in AgentEnum]
        for agent in possible_agents:
            mrl = self.ctx.tm.match_template(img, 'hollow', prefix + agent.agent_id, threshold=0.8)
            if mrl.max is not None:
                return agent

        return None

    def check_screen(self, screen: MatLike, screenshot_time: float,
                     check_battle_end: bool = True,
                     sync: bool = False) -> None:
        """
        异步判断角战斗画面
        :return:
        """
        future_list: List[Future] = []

        if check_battle_end:
            future_list.append(_hollow_context_executor.submit(self._check_battle_end, screen, screenshot_time))

        for future in future_list:
            future.add_done_callback(thread_utils.handle_future_result)

        if sync:
            for future in future_list:
                future.result()

    def _check_battle_end(self, screen: MatLike, screenshot_time: float) -> None:
        if not self._check_end_lock.acquire(blocking=False):
            return

        try:
            if screenshot_time - self._last_check_end_time < cal_utils.random_in_range(self._check_end_interval):
                # 还没有达到识别间隔
                return
            self._last_check_end_time = screenshot_time

            result1 = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                             screen_name='零号空洞-事件', area_name='战斗结果-确定')
            result2 = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                             screen_name='零号空洞-事件', area_name='背包')
            result3 = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                             screen_name='零号空洞-事件', area_name='通关-完成')
            self._last_check_end_result = ((result1 == FindAreaResultEnum.TRUE)
                                           or (result2 == FindAreaResultEnum.TRUE)
                                           or (result3 == FindAreaResultEnum.TRUE)
                                           )

        except Exception:
            log.error('识别战斗结束失败', exc_info=True)
        finally:
            self._check_end_lock.release()

    def is_battle_end(self) -> bool:
        return self._last_check_end_result


def __debug():
    ctx = ZContext()
    ctx.init_by_config()

    from one_dragon.utils import debug_utils
    img = debug_utils.get_debug_image('_1723263502457')
    agents = ctx.hollow.check_agent_list(img)
    print([i.agent_name for i in agents if i is not None])


if __name__ == '__main__':
    __debug()