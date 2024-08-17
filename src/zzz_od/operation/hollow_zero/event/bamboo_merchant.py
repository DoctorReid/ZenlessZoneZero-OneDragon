import time

import cv2
from typing import ClassVar

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.hollow_zero.event import event_utils
from zzz_od.operation.zzz_operation import ZOperation


class BambooMerchant(ZOperation):

    STATUS_LEVEL_1: ClassVar[str] = '外层选择'
    NOT_TO_BUY: ClassVar[str] = '不购买'

    def __init__(self, ctx: ZContext):
        """
        在邦布商人的画面了 尽量购买
        :param ctx:
        """
        ZOperation.__init__(
            self, ctx,
            node_max_retry_times=5,
            op_name=gt('邦布商人')
        )

    @node_from(from_name='购买后确定')
    @operation_node(name='画面识别', is_start_node=True)
    def check_screen(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = event_utils.get_event_text_area(self)

        result = self.round_by_ocr(screen, '鸣徽交易', area=area)
        if result.is_success:
            return self.round_success(BambooMerchant.STATUS_LEVEL_1)

        result = self.round_by_find_area(screen, '零号空洞-商店', '二级标题-鸣徽交易')
        if result.is_success:
            return result

        area = self.ctx.screen_loader.get_area('零号空洞-事件', '底部-选择列表')
        result = self.round_by_ocr_and_click(screen, '确定', area=area)
        if result.is_success:
            return self.round_wait(wait=1)

        return self.round_retry('未知画面', wait=1)

    @node_from(from_name='画面识别', status=STATUS_LEVEL_1)
    @operation_node(name='鸣徽交易')
    def choose_buy(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = event_utils.get_event_text_area(self)

        result = self.round_by_ocr_and_click(screen, '鸣徽交易', area=area)
        if result.is_success:
            return self.round_success(result.status, wait=1)

        result = self.round_by_ocr_and_click(screen, '特价折扣', area=area)
        if result.is_success:
            return self.round_success(result.status, wait=1)

        return self.round_retry(wait=1)

    @node_from(from_name='画面识别', status='二级标题-鸣徽交易')
    @node_from(from_name='鸣徽交易')
    @operation_node(name='选择鸣徽')
    def choose_item(self) -> OperationRoundResult:
        screen = self.screenshot()

        for idx in reversed(range(1, 4)):
            area = self.ctx.screen_loader.get_area('零号空洞-商店', ('商品价格-%d' % idx))

            part = cv2_utils.crop_image_only(screen, area.rect)
            mask = cv2.inRange(part, (240, 140, 0), (255, 255, 50))
            to_ocr = cv2.bitwise_and(part, part, mask=mask)

            ocr_result = self.ctx.ocr.run_ocr_single_line(to_ocr)
            digit = str_utils.get_positive_digits(ocr_result, None)
            if digit is None:
                continue

            self.ctx.controller.click(area.center)
            time.sleep(1)

            buy_area = self.ctx.screen_loader.get_area('零号空洞-商店', ('商品购买-%d' % idx))
            self.ctx.controller.click(buy_area.center)
            time.sleep(1)

            return self.round_success()

        return self.round_success(BambooMerchant.NOT_TO_BUY, wait=1)

    @node_from(from_name='选择鸣徽')
    @operation_node(name='购买后确定')
    def confirm(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '零号空洞-商店', '购买后确定',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='选择鸣徽', status=NOT_TO_BUY)
    @operation_node(name='返回')
    def back(self) -> OperationRoundResult:
        screen = self.screenshot()
        result1 = self.round_by_find_and_click_area(screen, '零号空洞-商店', '右上角-返回',
                                                    success_wait=1.5, retry_wait=1)

        if not result1.is_success:
            return self.round_retry(status=result1.status)

        return self.round_by_find_and_click_area(screen, '零号空洞-商店', '右上角-返回',
                                                 success_wait=1, retry_wait=1)
