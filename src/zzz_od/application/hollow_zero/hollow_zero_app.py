from typing import ClassVar

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.compendium.compendium_choose_tab import CompendiumChooseTab
from zzz_od.operation.compendium.tp_by_compendium import TransportByCompendium


class HollowZeroApp(ZApplication):

    STATUS_NO_REWARD: ClassVar[str] = '无奖励可领取'

    def __init__(self, ctx: ZContext):
        """
        每天自动接收邮件奖励
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='hollow_zero',
            op_name=gt('零号空洞', 'ui'),
            run_record=None
        )

    @operation_node(name='传送', is_start_node=False)
    def tp(self) -> OperationRoundResult:
        op = TransportByCompendium(self.ctx,
                                   '挑战',
                                   '零号空洞',
                                   '资质考核')
        return self.round_by_op(op.execute())

    @node_from(from_name='传送')
    @operation_node(name='等待入口加载')
    def wait_entry_loading(self) -> OperationRoundResult:
        self.node_max_retry_times = 20  # 等待加载久一点
        screen = self.screenshot()

        return self.round_by_find_area(screen, '零号空洞-入口', '街区', retry_wait=1)

    @node_from(from_name='等待入口加载')
    @operation_node(name='选择副本类型')
    def choose_mission_type(self) -> OperationRoundResult:
        self.node_max_retry_times = 5
        screen = self.screenshot()
        return self.round_by_ocr_and_click(screen, '旧都列车',
                                           success_wait=1, retry_wait=1)

    @node_from(from_name='选择副本类型')
    @operation_node(name='选择副本', is_start_node=True)
    def choose_mission(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('零号空洞-入口', '副本列表')
        return self.round_by_ocr_and_click(screen, '内部', area=area,
                                           success_wait=1, retry_wait=1)

    @node_from(from_name='选择副本')
    @operation_node(name='下一步')
    def click_next(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '零号空洞-入口', '下一步', success_wait=1, retry_wait=1)

    @node_from(from_name='下一步')
    @operation_node(name='出战')
    def click_deploy(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '零号空洞-入口', '出战', success_wait=1, retry_wait=1)


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    op = HollowZeroApp(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()