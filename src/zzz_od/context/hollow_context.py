import time
from concurrent.futures import ThreadPoolExecutor, Future

import cv2
import random
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
from zzz_od.hollow_zero.hollow_map import hollow_map_utils, hollow_pathfinding
from zzz_od.hollow_zero.hollow_map.hollow_pathfinding import RouteSearchRoute
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
        """
        识别地图信息
        :param screen: 游戏画面
        :param screenshot_time: 截图时间
        :return:
        """
        if self._event_model is None:
            return None
        result = self._event_model.run(screen, run_time=screenshot_time)
        # from zzz_od.yolo import detect_utils
        # cv2_utils.show_image(detect_utils.draw_detections(result), wait=0)
        if result is None:
            return None

        current_map = hollow_map_utils.construct_map_from_yolo_result(self.ctx, result, self.data_service.name_2_entry)

        # 仅保留最近2秒的地图识别结果
        self.map_results.append(current_map)
        while len(self.map_results) > 0 and screenshot_time - self.map_results[0].check_time > 2:
            self.map_results.pop(0)

        # 将多帧画面识别到的地图进行合并 可以互相补充识别不到的内容
        merge_map = hollow_map_utils.merge_map(self.ctx, self.map_results)

        return merge_map

    def get_next_to_move(self, current_map: HollowZeroMap) -> Optional[RouteSearchRoute]:
        """
        获取下一步的需要点击的节点
        :param current_map:
        :return:
        """
        if current_map.current_idx is None:
            return None
        idx_2_route = hollow_pathfinding.search_map(current_map, set(self._get_avoid()), self._visited_nodes)

        # 优先考虑 一步可达时前往
        route = hollow_pathfinding.get_route_in_1_step(idx_2_route, self._visited_nodes,
                                                       target_entry_list=self._get_go_in_1_step())
        if route is not None:
            log.info(f"优先级 [一步]")
            return route

        go_priority_list = self._get_waypoint()

        for to_go in go_priority_list:
            route = hollow_pathfinding.get_route_by_entry(idx_2_route, to_go, self._visited_nodes)
            if route is None:
                continue

            # 两次想要前往同一个节点
            if (self._last_route is not None
                    and hollow_pathfinding.is_same_node(self._last_route.node, route.node)):
                last_node = self._last_route.next_node_to_move
                curr_node = route.next_node_to_move
                if (hollow_pathfinding.is_same_node(last_node, curr_node)
                        and (
                                route.node.entry.entry_name in ['零号银行', '业绩考察点']  # 目标前往的点
                                and curr_node.entry.entry_name in ['门扉禁闭-财富', '门扉禁闭-善战']  # 下一步前往的格子是门
                        )
                ):
                    # 代表上一次点了之后 这次依然要点同样的位置 也就是无法通行
                    self.update_context_after_move(route.node)
                    continue

            self._last_route = route
            log.info(f"优先级 [途经]")
            return route

        # 是一定能走到的出口
        must_go_list = [
            '守门人',
            '传送点',
            '不宜久留'
        ]

        for to_go in must_go_list:
            route = hollow_pathfinding.get_route_by_entry(idx_2_route, to_go, self._visited_nodes)
            if route is not None:
                log.info(f"优先级 [终点]")
                return route

            # 如果之前走过，但走不到 说明可能中间有格子识别错了 这种情况就一格一格地走
            route = hollow_pathfinding.get_route_by_entry(idx_2_route, to_go, [])
            if route is not None:
                log.info(f"优先级 [终点]")
                route.go_way = 0
                return route
            
        # 随便找个一步可达的格子
        route = hollow_pathfinding.get_route_in_1_step(idx_2_route, self._visited_nodes,
                                                       target_entry_list=self.data_service.get_no_battle_list())
        if route is not None:
            log.info(f"优先级 [随机一步]")
            return route

        # 没有匹配到特殊点的时候 按副本类型走特定方向
        direction = 'w'
        if self.level_info.level >= 2 and self.level_info.phase == 1:
            direction = 'w'
        elif self.level_info.mission_type_name == '施工废墟':
            direction = 'd'
        elif self.level_info.mission_type_name == '巨厦遗骸':
            direction = 'd'

        route = hollow_pathfinding.get_route_by_direction(idx_2_route, direction)
        if route is not None:
            log.info(f"优先级 [方向]")
            return route

        # 兜底 走一步能到的
        route = hollow_pathfinding.get_route_in_1_step(idx_2_route, self._visited_nodes)
        if route is not None:
            log.info(f"优先级 [兜底]")
            return route

        # 最终兜底 随便移动一格
        current_node = current_map.nodes[current_map.current_idx]
        if hollow_pathfinding.is_same_node(self._last_current_node, current_node):
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
        fake_route = RouteSearchRoute(
            node=fake_node,
            node_idx=0,
            first_node=fake_node,
            first_need_step_node=fake_node,
            step_cnt=1,
            distance=0
        )
        log.info(f"优先级 [随机相邻]")
        return fake_route

    def update_context_after_move(self, node: HollowZeroMapNode) -> None:
        """
        点击后 更新
        :param node:
        :return:
        """
        visited = None
        for v in self._visited_nodes:
            if hollow_pathfinding.is_same_node(node, v):
                visited = v
                break

        if visited is not None:
            visited.visited_times += 1
        else:
            node.visited_times = 1
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

    def init_level_info(self, mission_type_name: str, mission_name: str,
                        level: int = 1, phase: int = 1) -> None:
        """
        重新开始空洞时 初始化空洞的信息
        """
        self.level_info = HollowLevelInfo(mission_type_name, mission_name, level, phase)

    def update_agent_list_after_support(self, new_agent: Agent, pos: int) -> None:
        """
        呼叫支援后 更新角色列表
        :param new_agent: 加入的代理人
        :param pos: 位置 1~3
        :return:
        """
        if self.agent_list is None:
            return
        idx = pos - 1
        if idx >= len(self.agent_list):
            return
        if self.agent_list[idx] is None:  # 接替的位置为空 直接赋值
            self.agent_list[idx] = new_agent
        else:
            none_idx: int = -1
            for i in range(len(self.agent_list)):
                if self.agent_list[i] is None:
                    none_idx = i
                    break

            if none_idx == -1:  # 原来就是满人 直接替换赋值
                self.agent_list[idx] = new_agent
            else:  # 原来不是满人 新加入的按位置赋值 原位置的角色移动到空位
                self.agent_list[none_idx] = self.agent_list[idx]
                self.agent_list[idx] = new_agent

    def had_been_entry(self, entry_name: str) -> bool:
        """
        是否曾经到达过某种类型的格子
        :param entry_name:
        :return:
        """
        for visited in self._visited_nodes:
            if visited.entry.entry_name == entry_name and visited.gt_max_visited_times:
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

    def check_info_before_move(self, screen: MatLike, current_map: HollowZeroMap):
        self.check_agent_list(screen, skip_if_checked=True)  # 平时可以不识别
        self._check_mission_level(screen, current_map)

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

    def check_agent_list(self, screen: MatLike, skip_if_checked: bool = False) -> Optional[List[Agent]]:
        """
        识别空洞画面里的角色列表
        """
        if skip_if_checked and self.agent_list is not None:
            return self.agent_list

        check: bool = False
        if self.agent_list is not None:
            check = self._check_agent_list_in_parallel(screen, self.agent_list)
        if not check: # 靠原来的识别不到 尝试全部识别
            self._check_agent_list_in_parallel(screen, None)

        return self.agent_list

    def _check_agent_list_in_parallel(self, screen: MatLike, possible_agents: Optional[List[Agent]] = None) -> bool:
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
            future_list.append(_hollow_context_executor.submit(self._match_agent_in, img, possible_agents))

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

        if any_not_none:  # 由于有空格存在 任意一个识别到就算ok
            self.agent_list = result_agent_list
            return True
        else:
            return False

    def init_before_hollow_start(self, mission_type_name: str, mission_name: str,
                                 level: int = 1, phase: int = 1) -> None:
        """
        进入空洞时 进行对应的初始化
        :return:
        """
        self.ctx.hollow.init_event_yolo(self.ctx.yolo_config.hollow_zero_event_gpu)
        self.init_level_info(mission_type_name, mission_name, level, phase)
        self.agent_list = None

def __debug_draw_detect():
    ctx = ZContext()
    ctx.init_by_config()

    from one_dragon.utils import debug_utils
    img = debug_utils.get_debug_image('event_1')

    ctx.hollow.init_event_yolo()
    result = ctx.hollow._event_model.run(img)
    from one_dragon.yolo import detect_utils
    result_img = detect_utils.draw_detections(result)
    cv2_utils.show_image(result_img, wait=0)
    cv2.destroyAllWindows()


def __debug_get_map():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    print(ctx.hollow_zero_challenge_config.module_name)

    from one_dragon.utils import debug_utils
    img_list = [
        '1',
    ]
    for i in img_list:
        screen = debug_utils.get_debug_image(i)

        ctx.hollow.init_event_yolo(False)
        current_map = ctx.hollow.check_current_map(screen, time.time())
        ctx.hollow.check_info_before_move(screen, current_map)

    idx_2_route = hollow_pathfinding.search_map(current_map, ctx.hollow._get_avoid(), [])
    route = ctx.hollow.get_next_to_move(current_map)
    next_node_to_move = route.next_node_to_move
    from zzz_od.hollow_zero.hollow_runner import HollowRunner
    runner = HollowRunner(ctx)
    to_click = runner.get_map_node_pos_to_click(screen, next_node_to_move)
    result_img = hollow_pathfinding.draw_map(screen, current_map,
                                             next_node=next_node_to_move, to_click=to_click,
                                             idx_2_route=idx_2_route,
                                             )
    cv2_utils.show_image(result_img, wait=0)
    cv2.destroyAllWindows()
    # print(current_map.contains_entry('业绩考察点'))
    print(next_node_to_move.pos)
    print(to_click)


def __screenshot_special():
    """
    对特定的节点进行截图
    @return:
    """
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.hollow.init_event_yolo(False)
    ctx.start_running()
    time.sleep(1)

    from one_dragon.utils import debug_utils
    while True:
        screen = ctx.controller.screenshot()
        current_map = ctx.hollow.check_current_map(screen, time.time())

        if not current_map.contains_entry('业绩考察点'):
            debug_utils.save_debug_image(screen)
            break

        if not ctx.is_context_running:
            break
        time.sleep(0.05)


if __name__ == '__main__':
    __debug_get_map()
    # __screenshot_special()

