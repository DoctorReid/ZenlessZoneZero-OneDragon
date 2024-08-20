import cv2
from cv2.typing import MatLike
from typing import ClassVar

from one_dragon.base.matcher.match_result import MatchResultList
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.hollow_zero.event import event_utils, resonium_utils
from zzz_od.operation.zzz_operation import ZOperation


class BambooMerchant(ZOperation):

    STATUS_LEVEL_1: ClassVar[str] = '外层选择'
    STATUS_LEVEL_2_BUY: ClassVar[str] = '二级标题-鸣徽交易'
    STATUS_LEVEL_2_UPGRADE: ClassVar[str] = '二级标题-鸣徽催化'
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

        area = self.ctx.screen_loader.get_area('零号空洞-商店', '二级标题')
        result = self.round_by_ocr(screen, '交易', area=area, lcs_percent=1)
        if result.is_success:
            return self.round_success(status=BambooMerchant.STATUS_LEVEL_2_BUY)

        result = self.round_by_ocr(screen, '催化', area=area, lcs_percent=1)
        if result.is_success:
            return self.round_success(status=BambooMerchant.STATUS_LEVEL_2_UPGRADE)

        area = self.ctx.screen_loader.get_area('零号空洞-事件', '底部-选择列表')
        result = self.round_by_ocr_and_click(screen, '确定', area=area)
        if result.is_success:
            return self.round_wait(wait=1)

        area = event_utils.get_event_text_area(self)
        result = self.round_by_ocr(screen, '鸣徽交易', area=area)
        if result.is_success:
            return self.round_success(BambooMerchant.STATUS_LEVEL_1)

        result = self.round_by_ocr(screen, '特价折扣', area=area)
        if result.is_success:
            return self.round_success(BambooMerchant.STATUS_LEVEL_1)

        return self.round_retry('未知画面', wait=1)

    @node_from(from_name='画面识别', status=STATUS_LEVEL_1)
    @operation_node(name='鸣徽交易')
    def choose_buy(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = event_utils.get_event_text_area(self)

        result = self.round_by_ocr_and_click(screen, '交易', area=area)
        if result.is_success:
            return self.round_success(BambooMerchant.STATUS_LEVEL_2_BUY, wait=1)

        result = self.round_by_ocr_and_click(screen, '特价折扣', area=area)
        if result.is_success:
            return self.round_success(result.status, wait=1)

        return self.round_retry(wait=1)

    @node_from(from_name='画面识别', status=STATUS_LEVEL_2_BUY)
    @node_from(from_name='鸣徽交易')
    @operation_node(name='选择鸣徽')
    def choose_item(self) -> OperationRoundResult:
        screen = self.screenshot()

        price_ocr_result_map = self._ocr_price_area(screen)
        price_pos_list = [i.max.center for i in price_ocr_result_map.values()]

        desc_ocr_result_map = self._ocr_desc_area(screen)
        item_list = []
        pos_list = []
        # 只保留有价格的
        for ocr_result, mrl in desc_ocr_result_map.items():
            item = self.ctx.hollow.data_service.match_resonium_by_ocr_name(ocr_result)
            if item is None:
                continue
            with_price: bool = False
            for price in price_pos_list:
                if price.y > mrl.max.center.y:
                    with_price = True
                    break

            if not with_price:
                continue
            item_list.append(item)
            pos_list.append(mrl.max.center)

        if len(item_list) > 0:
            idx_list = resonium_utils.choose_resonium_by_priority(item_list, self.ctx.hollow_zero_challenge_config.resonium_priority)
            to_choose = pos_list[idx_list[0]]
        else:
            to_choose = None
            for price in price_pos_list:
                if to_choose is None or price.y > to_choose.y:
                    to_choose = price

        if to_choose is None:
            return self.round_success(BambooMerchant.NOT_TO_BUY, wait=1)
        else:
            self.ctx.controller.click(to_choose)
            return self.round_success(wait=1)

    def _ocr_price_area(self, screen: MatLike) -> dict[str, MatchResultList]:
        area = self.ctx.screen_loader.get_area('零号空洞-商店', '商品价格区域')
        part = cv2_utils.crop_image_only(screen, area.rect)
        mask = cv2.inRange(part, (240, 140, 0), (255, 255, 50))
        mask = cv2_utils.dilate(mask, 5)
        to_ocr = cv2.bitwise_and(part, part, mask=mask)

        ocr_result_map = self.ctx.ocr.run_ocr(to_ocr)
        for mrl in ocr_result_map.values():
            mrl.add_offset(area.left_top)

        return ocr_result_map

    def _ocr_desc_area(self, screen: MatLike) -> dict[str, MatchResultList]:
        area = self.ctx.screen_loader.get_area('零号空洞-商店', '商品描述区域')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part)
        for mrl in ocr_result_map.values():
            mrl.add_offset(area.left_top)

        return ocr_result_map

    @node_from(from_name='选择鸣徽')
    @operation_node(name='购买')
    def buy(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '零号空洞-商店', '商品购买区域')

    @node_from(from_name='购买')
    @operation_node(name='购买后确定')
    def confirm(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '零号空洞-商店', '购买后确定',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='画面识别', status=STATUS_LEVEL_2_UPGRADE)
    @operation_node(name='鸣徽催化')
    def upgrade_resonium(self) -> OperationRoundResult:
        return self.round_success()

    @node_from(from_name='选择鸣徽', status=NOT_TO_BUY)
    @node_from(from_name='鸣徽催化')
    @operation_node(name='返回')
    def back(self) -> OperationRoundResult:
        screen = self.screenshot()
        result1 = self.round_by_find_and_click_area(screen, '零号空洞-商店', '右上角-返回',
                                                    success_wait=1.5, retry_wait=1)

        if not result1.is_success:
            return self.round_retry(status=result1.status)

        return self.round_by_find_and_click_area(screen, '零号空洞-商店', '右上角-返回',
                                                 success_wait=1, retry_wait=1)
