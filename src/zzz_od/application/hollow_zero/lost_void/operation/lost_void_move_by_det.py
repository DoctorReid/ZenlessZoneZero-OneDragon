import time

from cv2.typing import MatLike
from typing import List, Optional, ClassVar

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cal_utils
from one_dragon.yolo.detect_utils import DetectObjectResult, DetectFrameResult
from zzz_od.application.hollow_zero.lost_void.context.lost_void_detector import LostVoidDetector
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class MoveTargetWrapper:

    def __init__(self, detect_result: DetectObjectResult):
        self.is_mixed: bool = False  # 是否混合楼层
        self.target_name_list: List[str] = [detect_result.detect_class.class_name[5:]]
        self.target_rect_list: List[Rect] = [Rect(detect_result.x1, detect_result.y1, detect_result.x2, detect_result.y2)]

        self.leftest_target_name: str = self.target_name_list[0]  # 最左边的入口类型 也就是第一个遇到的区域
        self.entire_rect: Rect = self.target_rect_list[0]
        self.merge_parent = None  # 合并后的父节点

    def merge_another_target(self, other) -> bool:
        """
        尝试合并一个入口
        @return: 是否合并成功
        """
        if other.is_mixed and other.merge_parent is not None:
            other: MoveTargetWrapper = other.merge_parent

        this = self
        if this.is_mixed and this.merge_parent is not None:
            this: MoveTargetWrapper = this.merge_parent

        is_merge = False
        for x in this.target_rect_list:
            for y in other.target_rect_list:
                if cal_utils.distance_between(x.center, y.center) < x.width * 2:
                    is_merge = True
                    break

            if is_merge:
                break

        if is_merge:
            this.is_mixed = True
            other.is_mixed = True
            other.merge_parent = this

            this.target_name_list.extend(other.target_name_list)
            this.target_rect_list.extend(other.target_rect_list)

            leftest_entry_idx = 0
            x1 = this.target_rect_list[0].x1
            y1 = this.target_rect_list[0].y1
            x2 = this.target_rect_list[0].x2
            y2 = this.target_rect_list[0].y2
            for i in range(len(this.target_rect_list)):
                rect = this.target_rect_list[i]

                if rect.x1 < x1:
                    x1 = rect.x1
                    leftest_entry_idx = i
                if rect.x2 > x2:
                    x2 = rect.x2
                if rect.y1 < y1:
                    y1 = rect.y1
                if rect.y2 > y2:
                    y2 = rect.y2

            self.leftest_target_name = this.target_name_list[leftest_entry_idx]
            self.entire_rect = Rect(x1, y1, x2, y2)

        return is_merge


class LostVoidMoveByDet(ZOperation):

    STATUS_IN_BATTLE: ClassVar[str] = '遭遇战斗'

    def __init__(self, ctx: ZContext, target_type: str,
                 stop_when_interact: bool = True,
                 stop_when_disappear: bool = True):
        ZOperation.__init__(self, ctx, op_name=f'迷失之地-识别寻路-{target_type[5:]}')

        self.target_type: str = target_type
        self.stop_when_interact: bool = stop_when_interact  # 可交互时停止移动
        self.stop_when_disappear: bool = stop_when_disappear  # 目标消失时停止移动
        self.detector: LostVoidDetector = self.ctx.lost_void.detector

        self.last_target_result: Optional[MoveTargetWrapper] = None  # 最后一次识别到的目标
        self.last_target_name: Optional[str] = None  # 最后识别到的交互目标名称
        self.same_target_times: int = 0  # 识别到相同目标的次数
        self.stuck_times: int = 0  # 被困次数

    @node_from(from_name='移动', status='丢失目标')
    @node_from(from_name='脱困')
    @operation_node(name='移动前转向', node_max_retry_times=20, is_start_node=True)
    def turn_at_first(self) -> OperationRoundResult:
        screenshot_time = time.time()
        screen = self.screenshot()
        frame_result = self.detector.run(screen)

        if self.check_interact_stop(screen, frame_result):
            return self.round_success(data=self.last_target_name)

        target_result = self.get_move_target(frame_result)

        if target_result is None:
            # 识别不到目标的时候 判断是否在战斗
            in_battle = self.ctx.lost_void.check_battle_encounter(screen, screenshot_time)
            if in_battle:
                return self.round_fail(LostVoidMoveByDet.STATUS_IN_BATTLE)

            if self.stop_when_disappear:
                return self.round_fail('目标消失')

            # 没找到目标 转动
            self.ctx.controller.turn_by_distance(-100)
            return self.round_retry('未找到目标', wait=0.5)

        pos = target_result.entire_rect.center
        turn = self.turn_to_target(pos)
        if turn:
            return self.round_wait('转动朝向目标', wait=0.5)

        return self.round_success('开始移动')

    @node_from(from_name='移动前转向', status='开始移动')
    @operation_node(name='移动')
    def move_towards(self) -> OperationRoundResult:
        screenshot_time = time.time()
        screen = self.screenshot()
        frame_result: DetectFrameResult = self.detector.run(screen)

        if self.check_interact_stop(screen, frame_result):
            self.ctx.controller.stop_moving_forward()
            return self.round_success(data=self.last_target_name)

        target_result = self.get_move_target(frame_result)

        if target_result is None:
            self.ctx.controller.stop_moving_forward()

            # 识别不到目标的时候 判断是否在战斗
            in_battle = self.ctx.lost_void.check_battle_encounter(screen, screenshot_time)
            if in_battle:
                return self.round_fail(LostVoidMoveByDet.STATUS_IN_BATTLE)

            if self.stop_when_disappear:
                return self.round_success(data=self.last_target_name)
            else:
                return self.round_success(status='丢失目标', data=self.last_target_name)

        is_stuck = self.check_stuck(target_result)
        if is_stuck is not None:
            return is_stuck

        self.last_target_result = target_result
        self.last_target_name = target_result.leftest_target_name
        self.turn_to_target(target_result.entire_rect.center)
        self.ctx.controller.start_moving_forward()

        return self.round_wait('移动中', wait_round_time=0.1)

    def turn_to_target(self, target: Point) -> bool:
        """
        根据目标的位置 进行转动
        @param target: 目标位置
        @return: 是否进行了转动
        """
        if target.x < 850:
            self.ctx.controller.turn_by_distance(-50)
            return True
        elif target.x > 1000:
            self.ctx.controller.turn_by_distance(+50)
            return True
        else:
            return False

    def get_move_target(self, frame_result: DetectFrameResult) -> Optional[MoveTargetWrapper]:
        """
        获取移动目标

        @param frame_result: 当前帧识别结果
        @return:
        """
        if self.target_type != LostVoidDetector.CLASS_ENTRY:
            detect_result = self.detector.get_rightest_result(frame_result, self.target_type)
            if detect_result is not None:
                return MoveTargetWrapper(detect_result)
            else:
                return None
        else:
            return self.get_entry_target(frame_result)

    def get_entry_target(self, frame_result: DetectFrameResult) -> Optional[MoveTargetWrapper]:
        """
        获取入口目标 按优先级 尽量避免混合楼层

        @param frame_result: 当前帧识别结果
        @return:
        """
        entry_list: List[MoveTargetWrapper] = []
        for result in frame_result.results:
            if result.detect_class.class_name in [LostVoidDetector.CLASS_INTERACT, LostVoidDetector.CLASS_DISTANCE]:
                continue

            new_item = MoveTargetWrapper(result)
            entry_list.append(new_item)

        # 合并结果
        for x in entry_list:
            for y in entry_list:
                if x == y:
                    continue
                x.merge_another_target(y)

        # 筛选合并后的结果
        entry_list = [
            i
            for i in entry_list
            if i.merge_parent is None
        ]

        not_mixed_entry_list = [item for item in entry_list if not item.is_mixed]
        mixed_entry_list = [item for item in entry_list if item.is_mixed]
        if len(not_mixed_entry_list) > 0:
            return self.get_entry_target_by_priority(entry_list)
        elif len(mixed_entry_list) > 0:
            return self.get_entry_target_by_priority(mixed_entry_list)
        else:
            return None

    def get_entry_target_by_priority(self, entry_list: List[MoveTargetWrapper]) -> Optional[MoveTargetWrapper]:
        """
        按优先级 选择下层入口
        @param entry_list: 入口列表
        @return:
        """
        if entry_list is None or len(entry_list) == 0:
            return None

        return entry_list[0]

    def check_stuck(self, new_target: MoveTargetWrapper) -> Optional[OperationRoundResult]:
        """
        判断是否被困
        @return:
        """
        if self.last_target_result is None or new_target is None:
            self.same_target_times = 0
            return None

        if self.last_target_result.leftest_target_name != new_target.leftest_target_name:
            self.same_target_times = 0
            return None

        dis = cal_utils.distance_between(self.last_target_result.entire_rect.center, new_target.entire_rect.center)
        if dis < 20:
            self.same_target_times += 1

        if self.same_target_times >= 50:
            self.ctx.controller.stop_moving_forward()
            self.stuck_times += 1
            self.same_target_times = 0
            if self.stuck_times > 12:
                return self.round_fail('无法脱困')
            else:
                return self.round_success('尝试脱困')
        else:
            return None

    @node_from(from_name='移动', status='尝试脱困')
    @operation_node(name='脱困')
    def get_out_of_stuck(self) -> OperationRoundResult:
        """
        脱困
        @return:
        """
        if self.stuck_times % 6 == 1:  # 向左走
            self.ctx.controller.move_a(press=True, press_time=1, release=True)
        elif self.stuck_times % 6 == 2:  # 向右走
            self.ctx.controller.move_d(press=True, press_time=1, release=True)
        elif self.stuck_times % 6 == 3:  # 后左前 1秒
            self.ctx.controller.move_s(press=True, press_time=1, release=True)
            self.ctx.controller.move_a(press=True, press_time=1, release=True)
            self.ctx.controller.move_w(press=True, press_time=1, release=True)
        elif self.stuck_times % 6 == 4:  # 后右前 1秒
            self.ctx.controller.move_s(press=True, press_time=1, release=True)
            self.ctx.controller.move_d(press=True, press_time=1, release=True)
            self.ctx.controller.move_w(press=True, press_time=1, release=True)
        elif self.stuck_times % 6 == 5:  # 后左前 2秒
            self.ctx.controller.move_s(press=True, press_time=2, release=True)
            self.ctx.controller.move_a(press=True, press_time=2, release=True)
            self.ctx.controller.move_w(press=True, press_time=2, release=True)
        elif self.stuck_times % 6 == 0:  # 后右前 2秒
            self.ctx.controller.move_s(press=True, press_time=2, release=True)
            self.ctx.controller.move_d(press=True, press_time=2, release=True)
            self.ctx.controller.move_w(press=True, press_time=2, release=True)

        return self.round_success()

    def check_interact_stop(self, screen: MatLike, frame_result: DetectFrameResult) -> bool:
        """
        判断是否应该为交互停下来
        1. 要求出现交互时停下
        2. 出现交互按钮
        3. 有较大的可以交互的图标
        @param screen: 游戏画面
        @param frame_result: 识别结果
        @return:
        """
        if not self.stop_when_interact:
            return False

        result = self.round_by_find_area(screen, '战斗画面', '按键-交互')
        if not result.is_success:
            return False

        for result in frame_result.results:
            if result.detect_class.class_name == LostVoidDetector.CLASS_DISTANCE:
                # 不考虑 [距离]白点
                continue

            if result.width > 40 and result.height > 40:
                return True

        return False

    def handle_pause(self) -> None:
        ZOperation.handle_pause(self)
        self.ctx.controller.stop_moving_forward()