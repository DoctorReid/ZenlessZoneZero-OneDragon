import time
from concurrent.futures import ThreadPoolExecutor, Future

import cv2
import random
from cv2.typing import MatLike
from typing import List, Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils import cv2_utils, debug_utils, yolo_config_utils, str_utils
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

        self._only_boss_test_count: int = 0 # 速通尝试次数
        
        self._save_img:bool = False # 是否保存图片

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

    def get_next_to_move(self, current_map: HollowZeroMap) -> Optional[HollowZeroMapNode]:
        """
        获取下一步的移动方向
        :param current_map: 当前地图对象
        :return: 下一步需要前往的节点（如果没有则返回 None）
        """
        # 如果当前索引为空，无法继续移动，返回 None
        if current_map.current_idx is None:
            return None
    
        
        # 获取当前地图到各节点的路径信息
        idx_2_route = hollow_map_utils.search_map(current_map, self._get_avoid())

        # 优先检查是否有一步就能到达的目标节点
        route = hollow_map_utils.get_route_in_1_step(idx_2_route, self._visited_nodes,
                                                    target_entry_list=self._get_go_in_1_step())
        if route is not None:
            log.info(f"优先级 [一步]")
            return route.first_need_step_node

        # 查找优先要去的格子列表
        go_priority_list = self._get_waypoint()

        for to_go in go_priority_list:
            # 查找前往优先目标的路径
            route = hollow_map_utils.get_route_by_entry(idx_2_route, to_go, self._visited_nodes)
            if route is None:
                continue

            # 如果上次尝试到达同一节点，且无法通行则跳过该节点
            if (self._last_route is not None
                    and hollow_map_utils.is_same_node(self._last_route.node, route.node)):
                last_node = self._last_route.first_need_step_node
                curr_node = route.first_need_step_node
                # 如果当前和上次的第一个目标节点相同，并且节点为特定名称，代表无法通行，更新上下文后跳过
                if (hollow_map_utils.is_same_node(last_node, curr_node)
                        and (
                                curr_node.entry.entry_name in ['门扉禁闭-财富', '门扉禁闭-善战']
                                or route.node.entry.entry_name in ['零号银行', '业绩考察点']
                        )):
                    self.update_context_after_move(route.node)
                    continue

            # 更新上次路线，并返回当前目标
            self._last_route = route
            log.info(f"优先级 [途径]")
            return route.first_need_step_node

        # 针对速通的错误处理
        if self.ctx.hollow_zero_challenge_config.path_finding == HollowZeroChallengePathFinding.ONLY_BOSS.value.value:
            if current_map.search_entry("业绩考察点"):
                route = hollow_map_utils.get_route_by_entry(idx_2_route,"业绩考察点", self._visited_nodes)
                log.info(f"优先级 [速通]")
                if route is None:
                    if self._only_boss_test_count == -1:
                        self._only_boss_test_count = 0
                        pass
                    elif self._only_boss_test_count in (0,1):
                        info = ",".join([node.entry.entry_name for node in self._visited_nodes])
                        self._only_boss_test_count += 1
                        log.info(f"警告 第{self._only_boss_test_count}次尝试 寻路失败 已途径点信息如下 [{info}]")
                        # 保存地图信息
                        self._save_img = True
                        # 清空途径点
                        self._visited_nodes.clear()
                        # 伪造一个虚拟节点并返回
                        virtual_node = current_map.nodes[current_map.current_idx]
                        local = virtual_node.pos.center
                        fake_node = HollowZeroMapNode(
                            pos=Rect(local.x, local.y, local.x, local.y),
                            entry=HollowZeroEntry('0000-fake'),
                        )
                        return fake_node  
                else:
                    return route.first_need_step_node

        # 处理必须前往的特殊节点
        must_go_list = [
            '守门人',  # 守门人出口
            '传送点',  # 传送点
            '不宜久留'  # 特殊区域
        ]

        for to_go in must_go_list:
            route = hollow_map_utils.get_route_by_entry(idx_2_route, to_go, self._visited_nodes)
            if route is not None:
                log.info(f"优先级 [特殊]")
                return route.first_need_step_node

            # 如果曾经到过这个节点，但现在走不到，则尝试逐步靠近
            route = hollow_map_utils.get_route_by_entry(idx_2_route, to_go, [])
            if route is not None:
                log.info(f"优先级 [逼近]")
                return route.first_node

        # 根据副本类型选择默认方向（如需特殊处理）
        direction = 'w'
        if self.level_info.level >= 2 and self.level_info.phase == 1:
            direction = 'w'  # 默认向上
        elif self.level_info.mission_type_name == '施工废墟':
            direction = 'd'  # 施工废墟默认向右
        elif self.level_info.mission_type_name == '巨厦遗骸':
            direction = 'd'  # 巨厦遗骸默认向右

        # 根据指定方向获取路径
        route = hollow_map_utils.get_route_by_direction(idx_2_route, direction)
        if route is not None:
            log.info(f"优先级 [默认]")
            return route.first_need_step_node

        # 最后兜底：尝试找到一步能到的路径
        route = hollow_map_utils.get_route_in_1_step(idx_2_route, self._visited_nodes)
        if route is not None:
            log.info(f"优先级 [兜底]")
            return route.first_need_step_node

        # 如果仍然没有找到，随机选择一个方向进行移动
        current_node = current_map.nodes[current_map.current_idx]
        if hollow_map_utils.is_same_node(self._last_current_node, current_node):
            arr = ['w', 's', 'a', 'd']  # 上下左右四个方向
            arr.remove(direction)  # 移除当前方向
            direction = arr[random.randint(0, len(arr) - 1)]  # 随机选择其他方向
        self._last_current_node = current_node

        # 根据方向伪造一个节点前往
        if direction == 'w':
            to_go = current_node.pos.center - Point(0, current_node.pos.height)  # 向上
        elif direction == 's':
            to_go = current_node.pos.center + Point(0, current_node.pos.height)  # 向下
        elif direction == 'a':
            to_go = current_node.pos.center - Point(current_node.pos.width, 0)  # 向左
        else:
            to_go = current_node.pos.center + Point(current_node.pos.width, 0)  # 向右

        # 创建一个虚拟节点并返回
        fake_node = HollowZeroMapNode(
            pos=Rect(to_go.x, to_go.y, to_go.x, to_go.y),
            entry=HollowZeroEntry('0000-fake'),
        )
        log.info(f"优先级 [随机]")
        return fake_node

    def update_context_after_move(self, node: HollowZeroMapNode) -> None:
        """
        点击后 更新
        :param node:
        :return:
        """
        visited = None
        for v in self._visited_nodes:
            if hollow_map_utils.is_same_node(node, v):
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
        self.ctx.hollow.init_event_yolo(True)
        self.init_level_info(mission_type_name, mission_name, level, phase)
        self.agent_list = None

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
    print(ctx.hollow_zero_challenge_config.module_name)

    from one_dragon.utils import debug_utils
    img_list = [
        '_1725682732540',
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

