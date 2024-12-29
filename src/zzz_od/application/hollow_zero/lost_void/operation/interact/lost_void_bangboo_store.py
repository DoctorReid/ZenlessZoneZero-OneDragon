import time

import cv2
from cv2.typing import MatLike
from typing import List, Optional

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, cal_utils, str_utils
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

    @operation_node(name='等待加载', node_max_retry_times=10, is_start_node=True)
    def wait_loading(self) -> OperationRoundResult:
        screen_name = self.check_and_update_current_screen()
        if screen_name == '迷失之地-邦布商店':
            return self.round_success()
        else:
            return self.round_retry(status=f'当前画面 {screen_name}', wait=1)

    @node_from(from_name='等待加载')
    @node_from(from_name='确认后处理')
    @operation_node(name='购买藏品')
    def buy_artifact(self) -> OperationRoundResult:
        screen = self.screenshot()

        art_list = self.get_artifact_pos(screen)
        if len(art_list) == 0:
            return self.round_retry(status='未识别可购买藏品', wait=1)

        # TODO 加入优先级
        target_idx = 0
        self.ctx.controller.click(art_list[target_idx].buy_rect.center)
        return self.round_success(art_list[target_idx].artifact.name, wait=1)

    def get_artifact_pos(self, screen: MatLike) -> List[StoreItemWrapper]:
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

        result_list = [
            i
            for i in result_list
            if i.price is not None and i.buy_rect is not None
        ]
        display_text = ','.join([i.artifact.name for i in result_list])
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