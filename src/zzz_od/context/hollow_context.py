from concurrent.futures import ThreadPoolExecutor, Future

import cv2
import threading
from cv2.typing import MatLike
from typing import List, Optional, Union

from one_dragon.base.screen import screen_utils
from one_dragon.base.screen.screen_utils import FindAreaResultEnum
from one_dragon.utils import cv2_utils, thread_utils, cal_utils, os_utils
from one_dragon.utils.log_utils import log
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import Agent, AgentEnum
from zzz_od.hollow_zero.hollow_level_info import HollowLevelInfo
from zzz_od.hollow_zero.hollow_map import hollow_map_utils
from zzz_od.hollow_zero.hollow_map.hollow_zero_map import HollowZeroMap, HollowZeroMapNode
from zzz_od.operation.hollow_zero.hollow_zero_event import HallowZeroEventService
from zzz_od.yolo.hollow_event_detector import HollowEventDetector

_hollow_context_executor = ThreadPoolExecutor(thread_name_prefix='od_hollow_context', max_workers=16)


class HollowContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx
        self.agent_list: Optional[List[Agent]] = None

        self.event_service: HallowZeroEventService = HallowZeroEventService()
        self.level_info: HollowLevelInfo = HollowLevelInfo()

        self._event_model: Optional[HollowEventDetector] = None

        # 识别锁 保证每种类型只有1实例在进行识别
        self._check_end_lock = threading.Lock()

        # 识别间隔
        self._check_end_interval: Union[float, List[float]] = 5

        # 上一次识别的时间
        self._last_check_end_time: float = 0

        # 上一次识别的结果
        self.last_check_end_result: Optional[str] = None

    def init_battle_context(self,
                            check_end_interval: Union[float, List[float]] = 5,):
        # 识别间隔
        self._check_end_interval = check_end_interval

        # 上一次识别的时间
        self._last_check_end_time = 0

        # 上一次识别的结果
        self.last_check_end_result = None

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

            result = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                            screen_name='零号空洞-事件', area_name='挑战结果')
            if result == FindAreaResultEnum.TRUE:
                self.last_check_end_result = '挑战结果'
                return

            result = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                            screen_name='零号空洞-事件', area_name='背包')
            if result == FindAreaResultEnum.TRUE:
                self.last_check_end_result = '背包'
                return

            result = screen_utils.find_area(ctx=self.ctx, screen=screen,
                                            screen_name='零号空洞-事件', area_name='通关-完成')
            if result == FindAreaResultEnum.TRUE:
                self.last_check_end_result = '完成'
                return

            self.last_check_end_result = None

        except Exception:
            log.error('识别战斗结束失败', exc_info=True)
        finally:
            self._check_end_lock.release()

    def init_event_yolo(self, use_gpu: bool = False) -> None:
        if self._event_model is None or self._event_model.gpu != use_gpu:
            self._event_model = HollowEventDetector(
                model_parent_dir_path=os_utils.get_path_under_work_dir('assets', 'models', 'yolo'),
                gpu=use_gpu,
            )

    def clear_detect_history(self) -> None:
        """
        清除识别记录
        :return:
        """
        if self._event_model is None:
            return
        self._event_model.run_result_history.clear()

    def check_current_map(self, screen: MatLike) -> Optional[HollowZeroMap]:
        if self._event_model is None:
            return None
        result = self._event_model.run(screen)
        if result is None:
            return None

        current_map = hollow_map_utils.construct_map_from_yolo_result(self._event_model.run_result_history)

        # 填充类型相关信息
        for node in current_map.nodes:
            node.entry = self.event_service.get_entry_by_name(node.node_name)
        return current_map

    def check_before_move(self, screen: MatLike) -> None:
        """
        移动前 进行识别
        :param screen:
        :return:
        """
        if self.agent_list is None:
            self.check_agent_list(screen)

    def get_next_to_move(self, current_map: HollowZeroMap) -> Optional[HollowZeroMapNode]:
        """
        获取下一步的移动方向
        :param current_map:
        :return:
        """
        idx_2_route = hollow_map_utils.search_map(current_map)

        # 1步可到的奖励 都先领取了
        route = hollow_map_utils.get_route_in_1_step_benefit(idx_2_route)
        if route is not None:
            return current_map.nodes[route.first_step]

        # 队员不满的时候 优先去增援
        if self.ctx.hollow.agent_list is None or len(self.ctx.hollow.agent_list) < 3:
            route = hollow_map_utils.get_route_by_entry(idx_2_route, '呼叫增援')
            if route is not None:
                return current_map.nodes[route.first_step]

        # 有业绩的时候 去拿业绩
        route = hollow_map_utils.get_route_by_entry(idx_2_route, '业绩考察点')
        if route is not None:
            return current_map.nodes[route.first_step]

        # 有银行的时候 去银行
        route = hollow_map_utils.get_route_by_entry(idx_2_route, '零号银行')
        if route is not None:
            return current_map.nodes[route.first_step]

        # 有出口的时候 去出口
        route = hollow_map_utils.get_route_by_entry(idx_2_route, '守门人')
        if route is not None:
            return current_map.nodes[route.first_step]

        # 没有特殊点的时候 按副本类型走特定方向
        if self.level_info.level == 2:  # 第2层往上走
            route = hollow_map_utils.get_route_by_direction(idx_2_route, 'w')
            if route is not None:
                return current_map.nodes[route.first_step]

        return None

    def update_context_after_move(self, node: HollowZeroMapNode) -> None:
        """
        点击后 更新
        :param node:
        :return:
        """
        pass


def __debug_draw_detect():
    ctx = ZContext()
    ctx.init_by_config()

    from one_dragon.utils import debug_utils
    img = debug_utils.get_debug_image('event_1')

    ctx.hollow.init_event_yolo()
    result = ctx.hollow._event_model.run(img)
    from zzz_od.yolo import detect_utils
    result_img = detect_utils.draw_detections(result)
    cv2_utils.show_image(result_img, wait=0)
    cv2.destroyAllWindows()


def __debug_get_map():
    ctx = ZContext()
    ctx.init_by_config()

    from one_dragon.utils import debug_utils
    img = debug_utils.get_debug_image('event_1')

    ctx.hollow.init_event_yolo()
    current_map = ctx.hollow.check_current_map(img)
    target = ctx.hollow.get_next_to_move(current_map)
    result_img = hollow_map_utils.draw_map(img, current_map, next_node=target)
    cv2_utils.show_image(result_img, wait=0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    __debug_get_map()

