from typing import Optional, ClassVar

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.log_utils import log
from zzz_od.application.charge_plan.charge_plan_config import ChargePlanItem
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class CouponHandler(ZOperation):
    """
    处理家政券使用的操作
    """

    STATUS_COUPON_AVAILABLE: ClassVar[str] = '可以使用家政券'
    STATUS_CONTINUE_RUN_WITH_CHARGE: ClassVar[str] = '继续使用电量'

    def __init__(self, ctx: ZContext, plan: ChargePlanItem):
        ZOperation.__init__(self, ctx, op_name='处理家政券')
        self.plan: ChargePlanItem = plan
        self.coupon_num: Optional[int] = None
        self.can_use_times: int = 0

    @operation_node(name='识别家政券数量', is_start_node=True)
    def check_coupon_num(self) -> OperationRoundResult:
        screen = self.screenshot()

        area = self.ctx.screen_loader.get_area('家政券', '数量')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result = self.ctx.ocr.run_ocr_single_line(part)
        self.coupon_num = str_utils.get_positive_digits(ocr_result, None)
        if self.coupon_num is None:
            log.error('未识别到家政券数量')
            return self.round_success(CouponHandler.STATUS_CONTINUE_RUN_WITH_CHARGE)
        if self.coupon_num == 0:
            log.info('家政券数量为 0')
            return self.round_success(CouponHandler.STATUS_CONTINUE_RUN_WITH_CHARGE)

        log.info('家政券数量 %d', self.coupon_num)

        max_need_use_times = self.plan.plan_times - self.plan.run_times

        if self.coupon_num > max_need_use_times:
            self.coupon_num = max_need_use_times

        self.can_use_times = self.coupon_num

        return self.round_success(CouponHandler.STATUS_COUPON_AVAILABLE)

    @node_from(from_name='识别家政券数量', status=STATUS_COUPON_AVAILABLE)
    @node_from(from_name='关闭弹窗', status=STATUS_COUPON_AVAILABLE)
    @operation_node(name='使用')
    def use_coupon(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_and_click_area(screen, '家政券', '使用')
        if result.is_success:
            self.can_use_times -= 1
            self.ctx.charge_plan_config.add_plan_run_times(self.plan)
            return self.round_success(result.status, wait=0.5)

        return self.round_retry(result.status, wait=1)

    @node_from(from_name='使用')
    @operation_node(name='确认')
    def confirm_use_coupon(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_and_click_area(screen, '家政券', '确认')
        if result.is_success:
            return self.round_success(result.status, wait=0.5)

        return self.round_retry(result.status, wait=1)

    @node_from(from_name='确认')
    @operation_node(name='关闭弹窗')
    def close_coupon_window(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '家政券', '绳网信用')
        if result.is_success:
            self.ctx.controller.click(Point(1500, 200))
            if self.can_use_times == 0:
                if self.plan.run_times < self.plan.plan_times:
                    return self.round_success(CouponHandler.STATUS_CONTINUE_RUN_WITH_CHARGE)
                else:
                    # 如果券用完了且计划次数也完成了，则结束
                    return self.round_success()
            # 如果券没用完，继续使用
            return self.round_success(CouponHandler.STATUS_COUPON_AVAILABLE, wait=0.5)

        return self.round_retry(result.status, wait=1)
