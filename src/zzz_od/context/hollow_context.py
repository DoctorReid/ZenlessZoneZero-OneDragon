import time
from concurrent.futures import ThreadPoolExecutor, Future
import random

import cv2
from cv2.typing import MatLike
from typing import List, Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils import cv2_utils, yolo_config_utils, str_utils
from one_dragon.utils.log_utils import log
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import Agent, AgentEnum
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroEntry
from zzz_od.hollow_zero.hollow_level_info import HollowLevelInfo
from zzz_od.hollow_zero.hollow_map import hollow_map_utils
from zzz_od.hollow_zero.hollow_map.hollow_map_utils import RouteSearchRoute
from zzz_od.hollow_zero.hollow_map.hollow_zero_map import HollowZeroMap, HollowZeroMapNode
from zzz_od.hollow_zero.hollow_zero_challenge_config import HollowZeroChallengePathFinding
from zzz_od.hollow_zero.hollow_zero_data_service import HallowZeroDataService
from zzz_od.yolo.hollow_event_detector import HollowEventDetector

_hollow_context_executor = ThreadPoolExecutor(thread_name_prefix='od_hollow_context', max_workers=16)


class HollowContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx
        self.agent_list: Optional[List[Agent]] = None

        self.data_service: HallowZeroDataService = HallowZeroDataService()
        self.level_info: HollowLevelInfo = HollowLevelInfo()

        self._event_model: Optional[HollowEventDetector] = None

        self.map_results: List[HollowZeroMap] = []  # 识别的地图结果
        self._visited_nodes: List[HollowZeroMapNode] = []  # 已经去过的点
        self._last_route: Optional[RouteSearchRoute] = None  # 上一次想走的路
        self._last_current_node: Optional[HollowZeroMapNode] = None  # 上一次当前所在的点
        self.speed_up_clicked: bool = False  # 是否已经点击加速

    def check_agent_list(self, screen: MatLike) -> Optional[List[Agent]]:
        """
        识别空洞画面里的角色列表
        """
        check_agent_area = [
            self.ctx.screen_loader.get_area('零号空洞-事件', ('角色-%d' % i))
            for i in range(1, 4)
        ]
        area_img = [
            cv2_utils.crop_image_only(screen, i.rect)
            for i in check_agent_area
        ]

        result_agent_list: List[Optional[Agent]] = []
        future_list: List[Future] = []

        for img in area_img:
            future_list.append(_hollow_context_executor.submit(self._match_agent_in, img, self.agent_list))

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
        在候选列表中匹配角色
        :return:
        """
        prefix = 'avatar_'
        if possible_agents is None:
            possible_agents = [agent_enum.value for agent_enum in AgentEnum]
        for agent in possible_agents:
            if agent is None:
                continue
            mrl = self.ctx.tm.match_template(img, 'hollow', prefix + agent.agent_id, threshold=0.8)
            if mrl.max is not None:
                return agent

        return None

    def init_event_yolo(self, use_gpu: bool = False) -> None:
        if self._event_model is None or self._event_model.gpu != use_gpu:
            use_gh_proxy = self.ctx.env_config.is_ghproxy
            self._event_model = HollowEventDetector(
                model_name=self.ctx.yolo_config.hollow_zero_event,
                model_parent_dir_path=yolo_config_utils.get_model_category_dir('hollow_zero_event'),
                gh_proxy=use_gh_proxy,
                personal_proxy=None if use_gh_proxy else self.ctx.env_config.personal_proxy,
                gpu=use_gpu
            )

    def clear_detect_history(self) -> None:
        """
        清除识别记录
        :return:
        """
        if self._event_model is None:
            return
        self._event_model.run_result_history.clear()

    def check_current_map(self, screen: MatLike, screenshot_time: float) -> Optional[HollowZeroMap]:
        if self._event_model is None:
            return None
        result = self._event_model.run(screen, run_time=screenshot_time)
        # from zzz_od.yolo import detect_utils
        # cv2_utils.show_image(detect_utils.draw_detections(result), wait=0)
        if result is None:
            return None

        current_map = hollow_map_utils.construct_map_from_yolo_result(result, self.data_service.name_2_entry)

        self.map_results.append(current_map)
        while len(self.map_results) > 0 and screenshot_time - self.map_results[0].check_time > 2:
            self.map_results.pop(0)

        merge_map = hollow_map_utils.merge_map(self.map_results)

        return merge_map

    def check_before_move(self, screen: MatLike) -> None:
        """
        移动前 进行识别
        :param screen:
        :return:
        """
        if self.agent_list is None:
            self.check_agent_list(screen)
        if self.level_info is None or self.level_info.level is None:
            pass

    def get_next_to_move(self, current_map: HollowZeroMap) -> Optional[HollowZeroMapNode]:
        """
        获取下一步的移动方向
        :param current_map:
        :return:
        """
        if current_map.current_idx is None:
            return None
        idx_2_route = hollow_map_utils.search_map(current_map, self._get_avoid())

        # 一步可达时前往
        route = hollow_map_utils.get_route_in_1_step(idx_2_route, self._visited_nodes,
                                                     target_entry_list=self._get_go_in_1_step())
        if route is not None:
            return route.first_need_step_node

        # 有一些优先要去的格子
        go_priority_list = self._get_waypoint()

        for to_go in go_priority_list:
            route = hollow_map_utils.get_route_by_entry(idx_2_route, to_go, self._visited_nodes)
            if route is None:
                continue

            # 两次想要前往同一个节点
            if (self._last_route is not None
                    and hollow_map_utils.is_same_node(self._last_route.node, route.node)
            ):
                last_node = self._last_route.first_need_step_node
                curr_node = route.first_need_step_node
                if (hollow_map_utils.is_same_node(last_node, curr_node)
                        and route.node.entry.entry_name == '业绩考察点'):
                    # 代表上一次点了之后 这次依然要点同样的位置 也就是无法通行
                    self._visited_nodes.append(route.node)
                    continue

            self._last_route = route
            return route.first_need_step_node

        # 是一定能走到的出口
        must_go_list = [
            '守门人',
            '传送点',
            '不宜久留'
        ]

        for to_go in must_go_list:
            route = hollow_map_utils.get_route_by_entry(idx_2_route, to_go, self._visited_nodes)
            if route is not None:
                return route.first_need_step_node

            # 如果之前走过，但走不到 说明可能中间有格子识别错了 这种情况就一格一格地走
            route = hollow_map_utils.get_route_by_entry(idx_2_route, to_go, [])
            if route is not None:
                return route.first_node

        # 没有匹配到特殊点的时候 按副本类型走特定方向
        direction = 'w'
        if self.level_info.level >= 2 and self.level_info.phase == 1:
            direction = 'w'
        elif self.level_info.mission_type_name == '施工废墟':
            direction = 'd'
        elif self.level_info.mission_type_name == '巨厦遗骸':
            direction = 'd'

        route = hollow_map_utils.get_route_by_direction(idx_2_route, direction)
        if route is not None:
            return route.first_need_step_node

        # 兜底 走一步能到的
        route = hollow_map_utils.get_route_in_1_step(idx_2_route, self._visited_nodes)
        if route is not None:
            return route.first_need_step_node

        # 最终兜底 随便移动一格
        current_node = current_map.nodes[current_map.current_idx]
        if hollow_map_utils.is_same_node(self._last_current_node, current_node):
            arr = ['w', 's', 'a', 'd']
            arr.remove(direction)
            direction = arr[random.randint(0, len(arr) - 1)]
        self._last_current_node = current_node

        # 伪造一个节点前往
        if direction == 'w':
            to_go = current_node.pos.center - Point(0, current_node.pos.height)
        elif direction == 's':
            to_go = current_node.pos.center + Point(0, current_node.pos.height)
        elif direction == 'a':
            to_go = current_node.pos.center - Point(current_node.pos.width, 0)
        else:
            to_go = current_node.pos.center + Point(current_node.pos.width, 0)

        fake_node = HollowZeroMapNode(
            pos=Rect(to_go.x, to_go.y, to_go.x, to_go.y),
            entry=HollowZeroEntry('0000-fake'),
        )

        return fake_node

    def update_context_after_move(self, node: HollowZeroMapNode) -> None:
        """
        点击后 更新
        :param node:
        :return:
        """
        self._visited_nodes.append(node)

        if node.entry.is_tp:
            self._visited_nodes.clear()

            if node.entry.entry_name == '传送点':
                if self.level_info is not None:
                    self.level_info.to_next_phase()

    def update_to_next_level(self) -> None:
        """
        前往下一层了 更新信息
        """
        self._visited_nodes.clear()
        if self.level_info is not None:
            self.level_info.to_next_level()
        self._last_route = None

    def init_level_info(self, mission_type_name: str, mission_name: str) -> None:
        """
        重新开始空洞时 初始化空洞的信息
        """
        self.level_info = HollowLevelInfo(mission_type_name, mission_name, 1, 1)

    def update_agent_list_after_support(self, new_agent: Agent, pos: int) -> None:
        """
        呼叫支援后 更新角色列表
        :param new_agent: 加入的代理人
        :param pos: 位置 1~3
        :return:
        """
        if self.agent_list is None:
            return
        if pos - 1 >= len(self.agent_list):
            return
        self.agent_list[pos - 1] = new_agent

    def had_been_entry(self, entry_name: str) -> bool:
        """
        是否曾经到达过某种类型的格子
        :param entry_name:
        :return:
        """
        for visited in self._visited_nodes:
            if visited.entry.entry_name == entry_name:
                return True
        return False

    def _get_go_in_1_step(self) -> List[str]:
        """
        一步可达时前往
        :return:
        """
        if self.ctx.hollow_zero_challenge_config.path_finding == HollowZeroChallengePathFinding.DEFAULT.value.value:
            return self.data_service.get_default_go_in_1_step_entry_list()
        elif self.ctx.hollow_zero_challenge_config.path_finding == HollowZeroChallengePathFinding.ONLY_BOSS.value.value:
            return self.data_service.get_only_boss_go_in_1_step_entry_list()
        elif self.ctx.hollow_zero_challenge_config.path_finding == HollowZeroChallengePathFinding.CUSTOM.value.value:
            return self.ctx.hollow_zero_challenge_config.go_in_1_step
        else:
            return []

    def _get_waypoint(self) -> List[str]:
        """
        途经点
        :return:
        """
        if self.ctx.hollow_zero_challenge_config.path_finding == HollowZeroChallengePathFinding.DEFAULT.value.value:
            return self.data_service.get_default_waypoint_entry_list()
        elif self.ctx.hollow_zero_challenge_config.path_finding == HollowZeroChallengePathFinding.ONLY_BOSS.value.value:
            return self.data_service.get_only_boss_waypoint_entry_list()
        elif self.ctx.hollow_zero_challenge_config.path_finding == HollowZeroChallengePathFinding.CUSTOM.value.value:
            return self.ctx.hollow_zero_challenge_config.waypoint
        else:
            return []

    def _get_avoid(self) -> List[str]:
        """
        避免途经点
        :return:
        """
        if self.ctx.hollow_zero_challenge_config.path_finding == HollowZeroChallengePathFinding.DEFAULT.value.value:
            return self.data_service.get_default_avoid_entry_list()
        elif self.ctx.hollow_zero_challenge_config.path_finding == HollowZeroChallengePathFinding.ONLY_BOSS.value.value:
            return self.data_service.get_default_avoid_entry_list()
        elif self.ctx.hollow_zero_challenge_config.path_finding == HollowZeroChallengePathFinding.CUSTOM.value.value:
            return self.ctx.hollow_zero_challenge_config.avoid
        else:
            return []

    def check_info_before_move(self, screen: MatLike, current_map: HollowZeroMap) -> bool:
        self._check_agent_list(screen)
        self._check_mission_level(screen, current_map)

    def _check_agent_list(self, screen: MatLike) -> None:
        if self.agent_list is not None:
            return
        self.check_agent_list(screen)

    def _check_mission_level(self, screen: MatLike, current_map: HollowZeroMap) -> None:
        """
        如果之前没有初始化好副本信息 靠当前画面识别 断点继续时有用
        :param screen:
        :param current_map: 当前地图信息
        :return:
        """
        level_info = self.level_info
        if level_info.level == -1:  # 没有楼层信息 先识别
            area = self.ctx.screen_loader.get_area('零号空洞-事件', '当前层数')
            part = cv2_utils.crop_image_only(screen, area.rect)
            ocr_result = self.ctx.ocr.run_ocr_single_line(part)
            digit = str_utils.get_positive_digits(ocr_result, err=-1)
            level_info.level = digit

        if level_info.phase == -1 and level_info.level in [2, 3]:  # 没有阶段信息 先尝试识别
            if current_map.contains_entry('传送点'):
                level_info.phase = 1
            else:
                level_info.phase = 2
        else:  # 1楼固定只有1阶段
            level_info.phase = 1

        # 旧都列车
        if level_info.mission_type_name is None:
            if level_info.level in [2, 3] and level_info.phase == 1:
                if current_map.contains_entry('假面研究者'):
                    level_info.mission_type_name = '旧都列车'

        # 施工废墟
        if level_info.mission_type_name is None:
            if current_map.contains_entry('投机客') or current_map.contains_entry('门扉禁闭-财富'):
                level_info.mission_type_name = '施工废墟'


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
    ctx.ocr.init_model()

    from one_dragon.utils import debug_utils
    img_list = [
        '_1724930679038',
    ]
    for i in img_list:
        img = debug_utils.get_debug_image(i)

        ctx.hollow.init_event_yolo(False)
        current_map = ctx.hollow.check_current_map(img, time.time())
        ctx.hollow.check_info_before_move(img, current_map)

    idx_2_route = hollow_map_utils.search_map(current_map, ctx.hollow._get_avoid())
    target = ctx.hollow.get_next_to_move(current_map)
    result_img = hollow_map_utils.draw_map(img, current_map, next_node=target, idx_2_route=idx_2_route)
    cv2_utils.show_image(result_img, wait=0)
    cv2.destroyAllWindows()
    print(current_map.contains_entry('业绩考察点'))


if __name__ == '__main__':
    __debug_get_map()

