import time

import cv2
from cv2.typing import MatLike
from typing import List, Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from zzz_od.application.hollow_zero.lost_void.context.lost_void_artifact import LostVoidArtifact
from zzz_od.application.hollow_zero.lost_void.operation.interact.lost_void_choose_common import LostVoidChooseCommon
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class StoreItemWrapper:

    def __init__(self, art: LostVoidArtifact, rect: Rect):
        self.artifact: LostVoidArtifact = art
        self.artifact_rect: Rect = rect
        self.price: Optional[int] = None
        self.buy_rect: Optional[Rect] = None

    def add_price(self, price: int, rect: Rect) -> bool:
        """
        添加价格
        @return:
        """
        x_dis = abs(self.artifact_rect.center.x - rect.center.x)
        if x_dis >= self.artifact_rect.width:
            return False

        self.price = price
        return True

    def add_buy(self, rect: Rect) -> bool:
        """
        添加购买按钮
        @return:
        """
        x_dis = abs(self.artifact_rect.center.x - rect.center.x)
        if x_dis >= self.artifact_rect.width:
            return False

        self.buy_rect = rect
        return True


class LostVoidBangbooStore(ZOperation):

    def __init__(self, ctx: ZContext):
        ZOperation.__init__(self, ctx, op_name='迷失之地-邦布商店')

        self.refresh_times: int = 0  # 刷新次数

    @node_from(from_name='确认后处理')
    @operation_node(name='购买藏品', is_start_node=True)
    def buy_artifact(self) -> OperationRoundResult:
        area = self.ctx.screen_loader.get_area('迷失之地-邦布商店', '文本-详情')
        self.ctx.controller.mouse_move(area.center + Point(0, 100))
        time.sleep(0.1)

        screen = self.screenshot()

        # 按刷新之后的确认
        result = self.round_by_find_and_click_area(screen, '迷失之地-邦布商店', '按钮-刷新-确认')
        if result.is_success:
            self.refresh_times += 1
            return self.round_wait(result.status, wait=1)

        screen_name = self.check_and_update_current_screen()
        if screen_name != '迷失之地-邦布商店':
            # 进入本指令之前 有可能识别错画面
            return self.round_retry(status=f'当前画面 {screen_name}', wait=1)

        art_list: List[MatchResult] = self.get_artifact_pos(screen)
        if len(art_list) == 0:
            return self.round_retry(status='未识别可购买藏品', wait=1)

        priority_list: List[MatchResult] = self.ctx.lost_void.get_artifact_by_priority(
            art_list, 1,
            consider_priority_1=True, consider_priority_2=self.refresh_times > self.ctx.lost_void.challenge_config.buy_only_priority_1,
            consider_not_in_priority=self.refresh_times > self.ctx.lost_void.challenge_config.buy_only_priority_2,
        )

        if len(priority_list) == 0:
            result = self.round_by_find_and_click_area(screen, '迷失之地-邦布商店', '按钮-刷新-可用')
            if result.is_success:
                return self.round_wait(result.status, wait=1)

            # 不可以刷新了 就不管优先级都买了
            priority_list = self.ctx.lost_void.get_artifact_by_priority(art_list, len(art_list))

        if len(priority_list) == 0:
            return self.round_retry(status='按优先级选择藏品失败', wait=1)

        target: MatchResult = priority_list[0]
        self.ctx.controller.click(target.center)
        return self.round_success(target.data.name, wait=1)

    def get_artifact_pos(self, screen: MatLike) -> List[MatchResult]:
        """
        获取藏品的位置
        @param screen: 游戏画面
        @return: 识别到的藏品
        """
        result_list: List[StoreItemWrapper] = []

        # 识别藏品
        area = self.ctx.screen_loader.get_area('迷失之地-邦布商店', '区域-藏品名称')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part)
        for ocr_result, mrl in ocr_result_map.items():
            art = self.ctx.lost_void.match_artifact_by_ocr_full(ocr_result)
            if art is None:
                continue

            mr = mrl.max.rect
            mr.add_offset(area.left_top)
            result_list.append(StoreItemWrapper(art, mr))

        # 识别价格
        area = self.ctx.screen_loader.get_area('迷失之地-邦布商店', '区域-价格')
        part = cv2_utils.crop_image_only(screen, area.rect)
        mask = cv2.inRange(part, (200, 200, 200), (255, 255, 255))
        mask = cv2_utils.dilate(mask, 2)
        to_ocr = cv2.bitwise_and(part, part, mask=mask)
        ocr_result_map = self.ctx.ocr.run_ocr(to_ocr)
        for ocr_result, mrl in ocr_result_map.items():
            price = str_utils.get_positive_digits(ocr_result)
            if price is None:
                continue

            for mr in mrl:
                mr.add_offset(area.left_top)
                for result in result_list:
                    result.add_price(price, mr.rect)

        # 识别购买按钮
        area = self.ctx.screen_loader.get_area('迷失之地-邦布商店', '区域-购买按钮')
        part = cv2_utils.crop_image_only(screen, area.rect)
        mask = cv2.inRange(part, (200, 200, 200), (255, 255, 255))
        mask = cv2_utils.dilate(mask, 2)
        to_ocr = cv2.bitwise_and(part, part, mask=mask)
        ocr_result_map = self.ctx.ocr.run_ocr(to_ocr)
        for ocr_result, mrl in ocr_result_map.items():
            if not str_utils.find_by_lcs(gt('购买'), ocr_result):
                continue

            for mr in mrl:
                mr.add_offset(area.left_top)
                for result in result_list:
                    result.add_buy(mr.rect)

        result_list: List[MatchResult] = [
            MatchResult(1, i.buy_rect.x1, i.buy_rect.y1, i.buy_rect.width, i.buy_rect.height,
                        data=i.artifact)
            for i in result_list
            if i.price is not None and i.buy_rect is not None
        ]

        display_text = ','.join([i.data.display_name for i in result_list]) if len(result_list) > 0 else '无'
        log.info(f'当前识别藏品 {display_text}')

        return result_list

    @node_from(from_name='购买藏品')
    @operation_node(name='点击确认')
    def click_confirm(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='迷失之地-邦布商店', area_name='按钮-购买-确认',
                                                 success_wait=1, retry_wait=1,
                                                 until_not_find_all=[('迷失之地-邦布商店', '按钮-购买-确认')])

    @node_from(from_name='点击确认')
    @operation_node(name='确认后处理')
    def after_confirm(self) -> OperationRoundResult:
        """
        处理可能出现的武备升级环节
        @return:
        """
        screen = self.screenshot()
        screen_name = self.check_and_update_current_screen(screen)

        if screen_name == '迷失之地-通用选择':
            op = LostVoidChooseCommon(self.ctx)
            op_result = op.execute()
            if op_result.success:
                return self.round_wait(status='武备升级', wait=1)
            else:
                return self.round_retry(status='武备升级失败', wait=1)
        elif screen_name == '迷失之地-邦布商店':
            return self.round_success(status='迷失之地-邦布商店', wait=1)
        else:
            return self.round_retry(status=f'未知画面 {screen_name}', wait=1)

    @node_from(from_name='购买藏品', success=False)
    @operation_node(name='购买结束')
    def finish(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='迷失之地-邦布商店', area_name='按钮-返回',
                                                 success_wait=1, retry_wait=1,
                                                 until_not_find_all=[('迷失之地-邦布商店', '按钮-返回')])


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.lost_void.init_before_run()
    ctx.start_running()

    op = LostVoidBangbooStore(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()