import time

import cv2
from cv2.typing import MatLike
from typing import ClassVar, Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation import Operation
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.base.screen import screen_utils
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from one_dragon.yolo.detect_utils import DetectFrameResult
from zzz_od.application.hollow_zero.lost_void.context.lost_void_detector import LostVoidDetector
from zzz_od.application.hollow_zero.lost_void.lost_void_challenge_config import LostVoidRegionType
from zzz_od.application.hollow_zero.lost_void.operation.interact.lost_void_bangboo_store import LostVoidBangbooStore
from zzz_od.application.hollow_zero.lost_void.operation.interact.lost_void_choose_common import LostVoidChooseCommon
from zzz_od.application.hollow_zero.lost_void.operation.interact.lost_void_choose_gear import LostVoidChooseGear
from zzz_od.application.hollow_zero.lost_void.operation.interact.lost_void_choose_no_detail import \
    LostVoidChooseNoDetail
from zzz_od.application.hollow_zero.lost_void.operation.interact.lost_void_choose_no_num import LostVoidChooseNoNum
from zzz_od.application.hollow_zero.lost_void.operation.lost_void_move_by_det import LostVoidMoveByDet
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.challenge_mission.exit_in_battle import ExitInBattle
from zzz_od.operation.zzz_operation import ZOperation


class LostVoidRunLevel(ZOperation):

    STATUS_NEXT_LEVEL: ClassVar[str] = '进入下层'
    STATUS_COMPLETE: ClassVar[str] = '通关'

    IT_BATTLE: ClassVar[str] = 'xxxx-战斗'

    def __init__(self, ctx: ZContext, region_type: LostVoidRegionType):
        """
        层间移动

        非战斗区域
        1. 朝感叹号移动
        2. 朝距离白点移动
        3. 朝下层入口移动
        4. 1~3没有识别目标的话 识别右上角文本提示 看会不会进入战斗
        5. 1~3没有识别目标的话 角色血量条是否扣减 有的话代表进入了战斗

        朝距离白点移动后 可能会是进入了混合区域的下一个区域
        1. 看有没有识别目标 有的话回到非战斗区域逻辑
        2. 1没有识别目标的话 识别右上角文本提示 看会不会进入战斗
        3. 1没有识别目标的话 角色血量条是否扣减 有的话代表进入了战斗

        战斗区域
        1. 战斗
        2. 非战斗画面后的一次识别 进行一次目标识别 判断是否脱离了战斗

        成功则返回 data=下一个可能的区域类型
        @param ctx:
        @param region_type:
        """
        ZOperation.__init__(self, ctx, op_name='迷失之地-层间移动')

        self.region_type: LostVoidRegionType = region_type
        self.detector: LostVoidDetector = self.ctx.lost_void.detector
        self.auto_op: AutoBattleOperator = self.ctx.lost_void.auto_op
        self.nothing_times: int = 0  # 识别不到内容的次数
        self.target_interact_type: str = ''  # 目标交互类型
        self.interact_entry_name: str = ''  # 交互的下层入口名称

        self.last_frame_in_battle: bool = True  # 上一帧画面在战斗
        self.current_frame_in_battle: bool = True  # 当前帧画面在战斗
        self.last_det_time: float = 0  # 上一次进行识别的时间
        self.no_in_battle_times: int = 0  # 识别到不在战斗的次数
        self.last_check_finish_time: float = 0  # 上一次识别结束的时间
        self.talk_opt_idx = 0  # 交互选择的选项
        self.reward_eval_found: bool = False  # 挑战结果中可以识别到业绩点
        self.reward_dn_found: bool = False  # 挑战结果中可以识别到丁尼

    @node_from(from_name='非战斗画面识别', status='未在大世界')  # 有小概率交互入口后 没处理好结束本次RunLevel 重新从等待加载 开始
    @operation_node(name='等待加载', node_max_retry_times=60, is_start_node=True)
    def wait_loading(self) -> OperationRoundResult:
        screen = self.screenshot()

        if self.in_normal_world(screen):
            return self.round_success('大世界')

        # 在精英怪后后 点击完挑战结果后 加载挚友会谈前 可能会弹出奖励 因此在加载这里判断是否有奖励需要选择
        screen_name = self.check_and_update_current_screen(screen)
        if screen_name in ['迷失之地-武备选择', '迷失之地-通用选择']:
            self.target_interact_type = LostVoidDetector.CLASS_INTERACT
            return self.round_success(screen_name)

        # 挑战-限时 挑战-无伤都是这个 都是需要战斗
        result = self.round_by_find_and_click_area(screen, '迷失之地-大世界', '按钮-挑战-确认')
        if result.is_success:
            self.region_type = LostVoidRegionType.CHANLLENGE_TIME_TRAIL
            return self.round_wait(result.status)

        return self.round_retry('未找到攻击交互按键', wait=1)

    @node_from(from_name='等待加载')
    @operation_node(name='区域类型初始化')
    def init_for_region_type(self) -> OperationRoundResult:
        """
        根据区域类型 跳转到具体的识别逻辑
        @return:
        """
        if self.region_type == LostVoidRegionType.ENTRY:
            return self.round_success('非战斗区域')
        if self.region_type == LostVoidRegionType.COMBAT_RESONIUM:
            return self.round_success('战斗区域')
        if self.region_type == LostVoidRegionType.COMBAT_GEAR:
            return self.round_success('战斗区域')
        if self.region_type == LostVoidRegionType.COMBAT_COIN:
            return self.round_success('战斗区域')
        if self.region_type == LostVoidRegionType.CHANLLENGE_FLAWLESS:
            return self.round_success('战斗区域')
        if self.region_type == LostVoidRegionType.CHANLLENGE_TIME_TRAIL:
            return self.round_success('战斗区域')
        if self.region_type == LostVoidRegionType.ENCOUNTER:
            return self.round_success('非战斗区域')
        if self.region_type == LostVoidRegionType.PRICE_DIFFERENCE:
            return self.round_success('非战斗区域')
        if self.region_type == LostVoidRegionType.REST:
            return self.round_success('非战斗区域')
        if self.region_type == LostVoidRegionType.BANGBOO_STORE:
            return self.round_success('非战斗区域')
        if self.region_type == LostVoidRegionType.FRIENDLY_TALK:
            return self.round_success('非战斗区域')
        if self.region_type == LostVoidRegionType.ELITE:
            return self.round_success('战斗区域')
        if self.region_type == LostVoidRegionType.BOSS:
            return self.round_success('战斗区域')

        return self.round_success('非战斗区域')

    @node_from(from_name='区域类型初始化', status='非战斗区域')
    @node_from(from_name='非战斗画面识别', status=LostVoidDetector.CLASS_DISTANCE)  # 朝白点移动后重新循环
    @node_from(from_name='交互后处理', status='大世界')  # 目前交互之后都不会有战斗
    @node_from(from_name='战斗中', status='识别需移动交互')  # 战斗后出现距离 或者下层入口
    @node_from(from_name='尝试交互', success=False)  # 没能交互到
    @operation_node(name='非战斗画面识别', timeout_seconds=180)
    def non_battle_check(self) -> OperationRoundResult:
        now = time.time()
        screen = self.screenshot()

        frame_result: DetectFrameResult = self.ctx.lost_void.detector.run(screen, run_time=now)
        with_interact, with_distance, with_entry = self.ctx.lost_void.detector.is_frame_with_all(frame_result)

        if with_interact:
            self.nothing_times = 0
            self.target_interact_type = LostVoidDetector.CLASS_INTERACT
            op = LostVoidMoveByDet(self.ctx, self.region_type, LostVoidDetector.CLASS_INTERACT,
                                   stop_when_disappear=False)
            op_result = op.execute()
            if op_result.success:
                return self.round_success(LostVoidDetector.CLASS_INTERACT, wait=1)
            elif op_result.status == LostVoidMoveByDet.STATUS_IN_BATTLE:
                return self.round_success(LostVoidMoveByDet.STATUS_IN_BATTLE)
            else:
                return self.round_retry('移动失败')
        elif with_distance:
            self.nothing_times = 0
            self.target_interact_type = LostVoidDetector.CLASS_DISTANCE
            op = LostVoidMoveByDet(self.ctx, self.region_type, LostVoidDetector.CLASS_DISTANCE,
                                   stop_when_interact=False)
            op_result = op.execute()
            if op_result.success:
                return self.round_success(LostVoidDetector.CLASS_DISTANCE)
            elif op_result.status == LostVoidMoveByDet.STATUS_IN_BATTLE:
                return self.round_success(LostVoidMoveByDet.STATUS_IN_BATTLE)
            else:
                return self.round_retry('移动失败')
        elif with_entry:
            self.nothing_times = 0
            self.target_interact_type = LostVoidDetector.CLASS_ENTRY
            op = LostVoidMoveByDet(self.ctx, self.region_type, LostVoidDetector.CLASS_ENTRY,
                                   stop_when_disappear=False)
            op_result = op.execute()
            if op_result.success:
                self.interact_entry_name = op_result.data
                return self.round_success(LostVoidDetector.CLASS_ENTRY)
            elif op_result.status == LostVoidMoveByDet.STATUS_IN_BATTLE:
                return self.round_success(LostVoidMoveByDet.STATUS_IN_BATTLE)
            else:
                return self.round_retry('移动失败')
        else:
            in_battle = self.ctx.lost_void.check_battle_encounter(screen, now)
            if in_battle:
                self.last_det_time = time.time()
                self.last_check_finish_time = time.time()
                return self.round_success(status='进入战斗')

        self.ctx.controller.turn_by_distance(-100)
        self.nothing_times += 1

        if self.nothing_times >= 10 and not self.in_normal_world(screen):
            return self.round_success('未在大世界')

        if self.nothing_times >= 50:
            return self.round_fail('未发现目标')
        return self.round_wait(status='转动识别目标', wait=0.5)

    @node_from(from_name='非战斗画面识别', status=LostVoidDetector.CLASS_INTERACT)
    @node_from(from_name='非战斗画面识别', status=LostVoidDetector.CLASS_ENTRY)
    @operation_node(name='尝试交互')
    def try_interact(self) -> OperationRoundResult:
        """
        走到了交互点后 尝试交互
        @return:
        """
        screen = self.screenshot()
        result = self.round_by_find_area(screen, '战斗画面', '按键-交互')
        if result.is_success:
            self.ctx.controller.interact(press=True, press_time=0.2, release=True)
            return self.round_retry('交互', wait=1)

        if not self.in_normal_world(screen):  # 按键消失 说明开始加载了
            return self.round_success('交互成功')

        # 没有交互按钮 可能走过头了 尝试往后走
        self.ctx.controller.move_s(press=True, press_time=0.2, release=True)
        time.sleep(0.2)
        self.ctx.controller.move_s(press=True, press_time=0.2, release=True)
        time.sleep(0.2)
        self.ctx.controller.move_w(press=True, press_time=0.2, release=True)
        time.sleep(1)

        return self.round_retry('未发现交互按键')

    @node_from(from_name='等待加载', status='迷失之地-武备选择')
    @node_from(from_name='等待加载', status='迷失之地-通用选择')
    @node_from(from_name='尝试交互', status='交互成功')
    @node_from(from_name='战斗中', status='识别正在交互')
    @node_from(from_name='交互后处理', status='迷失之地-通用选择')
    @operation_node(name='交互处理')
    def handle_interact(self) -> OperationRoundResult:
        """
        只有以下情况确认交互完成

        1. 返回大世界
        2. 出现挑战结果
        @return:
        """
        screen = self.screenshot()

        screen_name = self.check_and_update_current_screen(screen)
        interact_op: Optional[ZOperation] = None
        if screen_name == '迷失之地-武备选择':
            interact_op = LostVoidChooseGear(self.ctx)
        elif screen_name == '迷失之地-通用选择':
            interact_op = LostVoidChooseCommon(self.ctx)
        elif screen_name == '迷失之地-无详情选择':
            interact_op = LostVoidChooseNoDetail(self.ctx)
        elif screen_name == '迷失之地-无数量选择':
            interact_op = LostVoidChooseNoNum(self.ctx)
        elif screen_name == '迷失之地-邦布商店':
            interact_op = LostVoidBangbooStore(self.ctx)
        elif screen_name == '迷失之地-大世界':
            return self.round_success('迷失之地-大世界')

        if interact_op is not None:
            # 出现选择的情况 交互到的不是下层入口 中途交互到其他内容了
            if self.target_interact_type == LostVoidDetector.CLASS_ENTRY:
                self.target_interact_type = LostVoidDetector.CLASS_INTERACT
            op_result = interact_op.execute()
            if op_result.success:
                return self.round_wait(op_result.status, wait=1)
            else:
                return self.round_fail(op_result.status)

        talk_result = self.try_talk(screen)
        if talk_result is not None:
            # 对话的情况 说明交互到的不是下层入口 中途交互到其他内容了
            if self.target_interact_type == LostVoidDetector.CLASS_ENTRY:
                self.target_interact_type = None

            return talk_result

        if self.in_normal_world(screen):
            return self.round_success('迷失之地-大世界')

        result = self.round_by_find_area(screen, '迷失之地-挑战结果', '标题-挑战结果')
        if result.is_success:
            return self.round_success('迷失之地-挑战结果')

        # 不在大世界的话 说明交互入口成功了
        if self.target_interact_type == LostVoidDetector.CLASS_ENTRY:
            return self.round_success(LostVoidRunLevel.STATUS_NEXT_LEVEL)

        # 交互后 可能出现了后续的交互
        return self.round_retry(status=f'未知画面', wait_round_time=1)

    def try_talk(self, screen: MatLike) -> OperationRoundResult:
        """
        判断是否在对话 并进行点击
        @return:
        """
        # 有对话名称的
        area = self.ctx.screen_loader.get_area('迷失之地-大世界', '区域-对话角色名称')
        part = cv2_utils.crop_image_only(screen, area.rect)
        mask = cv2.inRange(part, (200, 200, 200), (255, 255, 255))
        mask = cv2_utils.dilate(mask, 2)
        to_ocr = cv2.bitwise_and(part, part, mask=mask)
        ocr_result_map = self.ctx.ocr.run_ocr(to_ocr)

        if len(ocr_result_map) > 0:  # 有可能在交互
            # 判断是否有选项
            opt_result = self.try_talk_options(screen)
            if opt_result is not None:
                return opt_result

            self.ctx.controller.click(area.center + Point(0, 50))  # 往下一点点击 防止遮住了名称

            return self.round_wait(f'尝试交互 {str(list(ocr_result_map.keys()))}', wait=0.5)

        # 对话内容 特殊的 没有对话名称的
        area = self.ctx.screen_loader.get_area('迷失之地-大世界', '区域-对话内容')
        part = cv2_utils.crop_image_only(screen, area.rect)
        mask = cv2.inRange(part, (200, 200, 200), (255, 255, 255))
        mask = cv2_utils.dilate(mask, 2)
        to_ocr = cv2.bitwise_and(part, part, mask=mask)
        ocr_result_map = self.ctx.ocr.run_ocr(to_ocr)

        special_talk_list = [
            '似乎购买了充值卡就会得到齿轮硬币奖励，但是在离开之后身上的齿轮硬币都',  # 奸商布
            '（声音消失了，伸手从裂隙那头好像摸到了什么）',  # 零号业绩
        ]

        for ocr_result in ocr_result_map.keys():
            for special_talk in special_talk_list:
                if not str_utils.find_by_lcs(gt(special_talk), ocr_result):
                    continue

                # 判断是否有选项
                opt_result = self.try_talk_options(screen)
                if opt_result is not None:
                    return opt_result

                self.ctx.controller.click(area.center)
                return self.round_wait(f'尝试交互 {str(list(ocr_result_map.keys()))}', wait=0.5)

    def try_talk_options(self, screen: MatLike) -> Optional[OperationRoundResult]:
        """
        判断是否有对话选项
        @return:
        """
        area = self.ctx.screen_loader.get_area('迷失之地-大世界', '区域-右侧对话选项')
        part = cv2_utils.crop_image_only(screen, area.rect)
        mask = cv2.inRange(part, (200, 200, 200), (255, 255, 255))
        mask = cv2_utils.dilate(mask, 2)
        to_ocr = cv2.bitwise_and(part, part, mask=mask)
        # cv2_utils.show_image(to_ocr, wait=0)
        ocr_result_map = self.ctx.ocr.run_ocr(to_ocr)

        ocr_result_list = []
        mr_list = []
        for ocr_result, mrl in ocr_result_map.items():
            if mrl.max is None:
                continue

            for mr in mrl:
                mr_list.append(mr)
                ocr_result_list.append(ocr_result)

        if len(mr_list) > 0:
            to_click_mr = mr_list[self.talk_opt_idx] if self.talk_opt_idx < len(mr_list) else mr_list[0]
            to_click_ocr_result = ocr_result_list[self.talk_opt_idx] if self.talk_opt_idx < len(ocr_result_list) else ocr_result_list[0]
            to_click_mr.add_offset(area.left_top)

            self.ctx.controller.click(to_click_mr.center)
            self.talk_opt_idx += 1
            return self.round_wait(f'尝试交互选项 {to_click_ocr_result}', wait=0.5)
        else:
            self.talk_opt_idx = 0

        # 有可能选项里只有符号 识别不到 这时候用图标识别兜底

        result = self.round_by_find_and_click_area(screen, '迷失之地-大世界', '区域-右侧对话图标')
        if result.is_success:
            return self.round_wait(f'尝试交互选项图标', wait=0.5)

    @node_from(from_name='交互处理', status='迷失之地-大世界')
    @node_from(from_name='交互处理', status='迷失之地-挑战结果')
    @node_from(from_name='交互处理', status=STATUS_NEXT_LEVEL)
    @node_from(from_name='交互处理', success=False, status='未知画面')
    @operation_node(name='交互后处理', node_max_retry_times=10)
    def after_interact(self) -> OperationRoundResult:
        """
        交互后
        1. 在大世界的 先退后 让交互按键消失 再继续后续寻路
        2. 不在大世界的 可能是战斗后结果画面 也可能是交互进入下层
        @return:
        """
        screen = self.screenshot()

        if self.in_normal_world(screen):
            self.move_after_interact()
            return self.round_success(status='大世界', wait=1)

        result = self.round_by_find_area(screen, '迷失之地-挑战结果', '标题-挑战结果')
        if result.is_success:
            # 这个标题出来之后 按钮还需要一段时间才能出来
            r2 = self.round_by_find_area(screen, '迷失之地-挑战结果', '按钮-确定')
            if r2.is_success:
                return self.round_success('挑战结果-确定', wait=2)

            r2 = self.round_by_find_area(screen, '迷失之地-挑战结果', '按钮-完成')
            if r2.is_success:
                return self.round_success('挑战结果-完成', wait=2)

        if self.target_interact_type == LostVoidDetector.CLASS_ENTRY:
            return self.round_success(LostVoidRunLevel.STATUS_NEXT_LEVEL, data=self.interact_entry_name)

        return self.round_retry('等待画面返回', wait=1)

    def in_normal_world(self, screen: MatLike) -> bool:
        """
        判断当前画面是否在大世界里
        @param screen: 游戏画面
        @return:
        """
        result = self.round_by_find_area(screen, '战斗画面', '按键-普通攻击')
        if result.is_success:
            return True

        result = self.round_by_find_area(screen, '战斗画面', '按键-交互')
        if result.is_success:
            return True

        result = self.round_by_find_area(screen, '迷失之地-大世界', '按键-交互-不可用')
        if result.is_success:
            return True

        return False

    def move_after_interact(self) -> None:
        """
        交互后 进行的特殊移动
        :return:
        """
        if self.target_interact_type == LostVoidRunLevel.IT_BATTLE:  # 战斗后的交互 不需要往后走
            return

        if self.region_type == LostVoidRegionType.ENTRY:
            # 第一层 两个武备选择后 往后走 可以方便走上楼梯
            self.ctx.controller.move_s(press=True, press_time=1, release=True)
        elif self.region_type == LostVoidRegionType.FRIENDLY_TALK:
            # 挚友会谈 交互从左往右 每次交互之后 向右移动 可以避开中间桌子的障碍
            self.ctx.controller.move_s(press=True, press_time=1, release=True)
            self.ctx.controller.move_d(press=True, press_time=1, release=True)
        elif self.target_interact_type == LostVoidDetector.CLASS_INTERACT:
            # 感叹号的情况 由于奸商布的位置和商店很靠近 因此固定交互后往后移动
            self.ctx.controller.move_s(press=True, press_time=1, release=True)

    @node_from(from_name='区域类型初始化', status='战斗区域')
    @node_from(from_name='非战斗画面识别', status='进入战斗')
    @node_from(from_name='非战斗画面识别', status=LostVoidMoveByDet.STATUS_IN_BATTLE)
    @operation_node(name='战斗中', mute=True, timeout_seconds=600)
    def in_battle(self) -> OperationRoundResult:
        if not self.auto_op.is_running:
            self.auto_op.start_running_async()

        screenshot_time = time.time()
        screen = self.screenshot()
        self.last_frame_in_battle = self.current_frame_in_battle
        self.current_frame_in_battle = self.auto_op.auto_battle_context.check_battle_state(screen, screenshot_time)

        if self.current_frame_in_battle:  # 当前回到可战斗画面
            if (not self.last_frame_in_battle  # 之前在非战斗画面
                or screenshot_time - self.last_det_time >= 1  # 1秒识别一次
                or (self.no_in_battle_times > 0 and screenshot_time - self.last_check_finish_time >= 0.1)  # 之前也识别到脱离战斗 0.1秒识别一次
            ):
                # 尝试识别目标
                self.last_det_time = screenshot_time
                no_in_battle = False
                try:
                    screen2 = self.screenshot()
                    # 为了不随意打断战斗 这里的识别阈值要高一点
                    frame_result: DetectFrameResult = self.detector.run(screen2, run_time=screenshot_time, conf=0.9)
                    with_interact, with_distance, with_entry = self.detector.is_frame_with_all(frame_result)
                    if with_interact or with_distance or with_entry:
                        no_in_battle = True
                except Exception as e:
                    # 刚开始可能有一段时间识别报错 有可能是一张图同时在两个onnx里面跑 加入第二次截图观察
                    log.error('战斗中识别交互出现异常', exc_info=e)
                    return self.round_wait()

                if not no_in_battle:
                    area = self.ctx.screen_loader.get_area('迷失之地-大世界', '区域-文本提示')
                    if screen_utils.find_by_ocr(self.ctx, screen2, target_cn='前往下一个区域', area=area):
                        no_in_battle = True

                if no_in_battle:
                    self.no_in_battle_times += 1
                else:
                    self.no_in_battle_times = 0

                if self.no_in_battle_times >= 10:
                    auto_battle_utils.stop_running(self.auto_op)
                    log.info('识别需移动交互')
                    return self.round_success('识别需移动交互')

                return self.round_wait(wait_round_time=self.ctx.battle_assistant_config.screenshot_interval)
        else:  # 当前不在战斗画面
            if (screenshot_time - self.last_check_finish_time >= 1  # 1秒识别一次
                or (self.no_in_battle_times > 0 and screenshot_time - self.last_check_finish_time >= 0.1) # 之前也识别到脱离战斗 0.1秒识别一次
            ):
                self.last_check_finish_time = screenshot_time
                possible_screen_name_list = [
                    '迷失之地-武备选择', '迷失之地-通用选择', '迷失之地-无详情选择', '迷失之地-无数量选择',
                    '迷失之地-挑战结果',
                    '迷失之地-大世界',  # 有可能是之前交互识别错了 认为进入了战斗楼层 实际上没有交互
                    '迷失之地-战斗失败'
                ]
                screen_name = self.check_and_update_current_screen(screen, possible_screen_name_list)
                if screen_name in possible_screen_name_list:
                    self.no_in_battle_times += 1
                else:
                    self.no_in_battle_times = 0

                if self.no_in_battle_times >= 10:
                    auto_battle_utils.stop_running(self.auto_op)

                    if screen_name == '迷失之地-战斗失败':
                        return self.round_success(screen_name)
                    else:
                        self.target_interact_type = LostVoidRunLevel.IT_BATTLE
                        log.info('识别正在交互')
                        return self.round_success('识别正在交互')

                return self.round_wait(wait_round_time=self.ctx.battle_assistant_config.screenshot_interval)

        return self.round_wait(wait_round_time=self.ctx.battle_assistant_config.screenshot_interval)

    @node_from(from_name='交互后处理', status='挑战结果-确定')
    @operation_node(name='挑战结果处理确定')
    def handle_challenge_result_confirm(self) -> OperationRoundResult:
        result = self.round_by_find_and_click_area(screen_name='迷失之地-挑战结果', area_name='按钮-确定',
                                                   until_not_find_all=[('迷失之地-挑战结果', '按钮-确定')],
                                                   success_wait=1, retry_wait=1)
        if result.is_success:
            return self.round_success(LostVoidRunLevel.STATUS_NEXT_LEVEL, data=LostVoidRegionType.FRIENDLY_TALK.value.value)
        else:
            return result

    @node_from(from_name='交互后处理', status='挑战结果-完成')
    @operation_node(name='挑战结果处理完成')
    def handle_challenge_result_finish(self) -> OperationRoundResult:
        screen = self.screenshot()

        # 由于有动画效果 这里需要识别很多轮 只要有一轮识别到就算有
        result = self.round_by_find_area(screen, '迷失之地-挑战结果', '奖励-零号业绩')
        if result.is_success:
            self.reward_eval_found = True
        result = self.round_by_find_area(screen, '迷失之地-挑战结果', '奖励-丁尼')
        if result.is_success:
            self.reward_dn_found = True

        result = self.round_by_find_and_click_area(screen=screen, screen_name='迷失之地-挑战结果', area_name='按钮-完成',
                                                   until_not_find_all=[('迷失之地-挑战结果', '按钮-完成')],
                                                   success_wait=1, retry_wait=1)
        if result.is_success:
            if self.reward_eval_found:
                # 有业绩点 说明两个都没达成
                self.ctx.lost_void_record.eval_point_complete = False
                self.ctx.lost_void_record.period_reward_complete = False
            else:
                self.ctx.lost_void_record.eval_point_complete = True
                self.ctx.lost_void_record.period_reward_complete = not self.reward_dn_found

            if self.ctx.lost_void_record.period_reward_complete:
                if self.ctx.env_config.is_debug:
                    self.save_screenshot(prefix='period_reward_complete')

            return self.round_success(LostVoidRunLevel.STATUS_COMPLETE, data=LostVoidRegionType.FRIENDLY_TALK.value.value)
        else:
            return result

    @node_from(from_name='非战斗画面识别', success=False, status=Operation.STATUS_TIMEOUT)
    @node_from(from_name='战斗中', success=False, status=Operation.STATUS_TIMEOUT)
    @operation_node(name='失败退出空洞')
    def fail_exit_lost_void(self) -> OperationRoundResult:
        auto_battle_utils.stop_running(self.auto_op)
        op = ExitInBattle(self.ctx, '迷失之地-挑战结果', '按钮-完成')
        return self.round_by_op_result(op.execute())

    @node_from(from_name='战斗中', status='迷失之地-战斗失败')
    @operation_node(name='处理战斗失败')
    def handle_battle_fail(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='迷失之地-战斗失败', area_name='按钮-撤退',
                                                 until_not_find_all=[('迷失之地-战斗失败', '按钮-撤退')],
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='失败退出空洞')
    @node_from(from_name='处理战斗失败')
    @operation_node(name='点击失败退出完成')
    def handle_fail_exit(self) -> OperationRoundResult:
        result = self.round_by_find_and_click_area(screen_name='迷失之地-挑战结果', area_name='按钮-完成',
                                                 until_not_find_all=[('迷失之地-挑战结果', '按钮-完成')],
                                                 success_wait=1, retry_wait=1)

        if result.is_success:
            return self.round_success(LostVoidRunLevel.STATUS_COMPLETE, data=LostVoidRegionType.ENTRY.value.value)
        else:
            return result

    def handle_pause(self) -> None:
        ZOperation.handle_pause(self)
        auto_battle_utils.stop_running(self.auto_op)


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.lost_void.init_before_run()
    ctx.ocr.init_model()
    ctx.start_running()

    op = LostVoidRunLevel(ctx, LostVoidRegionType.ENTRY)

    from one_dragon.utils import debug_utils
    screen = debug_utils.get_debug_image('_1736065936380')
    area = op.ctx.screen_loader.get_area('迷失之地-大世界', '区域-文本提示')
    print(screen_utils.find_by_ocr(op.ctx, screen, target_cn='前往下一个区域', area=area))


if __name__ == '__main__':
    __debug()
