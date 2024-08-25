import time

from typing import ClassVar

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.compendium.tp_by_compendium import TransportByCompendium
from zzz_od.operation.hollow_zero.hollow_runner import HollowRunner


class HollowZeroApp(ZApplication):

    STATUS_NO_REWARD: ClassVar[str] = '无奖励可领取'
    STATUS_TIMES_FINISHED: ClassVar[str] = '完成指定次数'

    def __init__(self, ctx: ZContext):
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='hollow_zero',
            op_name=gt('零号空洞', 'ui'),
            run_record=None
        )

        self.mission_name: str = '内部'
        self.mission_type_name: str = '旧都列车'

    def handle_init(self):
        mission_name = self.ctx.hollow_zero_config.mission_name
        idx = mission_name.find('-')
        if idx != -1:
            self.mission_name = mission_name
            self.mission_type_name = mission_name[:idx]
        else:
            self.mission_name = mission_name
            self.mission_type_name = mission_name

    @operation_node(name='传送', is_start_node=True)
    def tp(self) -> OperationRoundResult:
        op = TransportByCompendium(self.ctx,
                                   '挑战',
                                   '零号空洞',
                                   '资质考核')
        return self.round_by_op(op.execute())

    @node_from(from_name='传送')
    @node_from(from_name='自动运行')
    @operation_node(name='等待入口加载')
    def wait_entry_loading(self) -> OperationRoundResult:
        self.node_max_retry_times = 20  # 等待加载久一点
        screen = self.screenshot()

        return self.round_by_find_area(screen, '零号空洞-入口', '街区', retry_wait=1)

    @node_from(from_name='等待入口加载')
    @operation_node(name='选择副本类型')
    def choose_mission_type(self) -> OperationRoundResult:
        self.node_max_retry_times = 5
        if self.ctx.hollow_zero_record.is_finished_by_times():
            return self.round_success(HollowZeroApp.STATUS_TIMES_FINISHED)
        screen = self.screenshot()
        return self.round_by_ocr_and_click(screen, self.mission_type_name,
                                           success_wait=1, retry_wait=1)

    @node_from(from_name='选择副本类型')
    @operation_node(name='选择副本')
    def choose_mission(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('零号空洞-入口', '副本列表')
        return self.round_by_ocr_and_click(screen, self.mission_name, area=area,
                                           success_wait=1, retry_wait=1)

    @node_from(from_name='选择副本')
    @operation_node(name='下一步')
    def click_next(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_and_click_area(screen, '零号空洞-入口', '下一步')
        if result.is_success:
            return self.round_success(wait=1)

        result = self.round_by_find_and_click_area(screen, '零号空洞-入口', '行动中-确认')
        if result.is_success:
            return self.round_wait(wait=1)

        return self.round_retry(wait=1)

    @node_from(from_name='下一步')
    @operation_node(name='继续或出战')
    def continue_or_deploy(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_and_click_area(screen, '零号空洞-入口', '继续-确认')
        if result.is_success:
            return self.round_success(wait=1)

        result = self.round_by_find_and_click_area(screen, '零号空洞-入口', '出战')
        if result.is_success:
            return self.round_success(wait=1)

        return self.round_retry(wait=1)

    @node_from(from_name='继续或出战')
    @operation_node(name='自动运行')
    def auto_run(self) -> OperationRoundResult:
        self.ctx.hollow.init_level_info(self.mission_type_name, self.mission_name)
        self.ctx.hollow.init_event_yolo(True)
        op = HollowRunner(self.ctx)
        return self.round_by_op(op.execute())

    @node_from(from_name='选择副本类型', status=STATUS_TIMES_FINISHED)
    @operation_node(name='完成后等待加载')
    def wait_back_loading(self) -> OperationRoundResult:
        self.node_max_retry_times = 20  # 等待加载久一点
        screen = self.screenshot()

        return self.round_by_find_area(screen, '零号空洞-入口', '街区', retry_wait=1)

    @node_from(from_name='完成后等待加载')
    @operation_node(name='点击奖励入口')
    def click_reward_entry(self) -> OperationRoundResult:
        self.node_max_retry_times = 5

        return self.round_by_click_area('零号空洞-入口', '奖励入口', success_wait=1)

    @node_from(from_name='点击奖励入口')
    @operation_node(name='悬赏委托')
    def click_task(self) -> OperationRoundResult:
        self.node_max_retry_times = 5
        screen = self.screenshot()

        return self.round_by_find_and_click_area(screen, '零号空洞-入口', '悬赏委托',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='悬赏委托')
    @operation_node(name='领取奖励')
    def claim_reward(self) -> OperationRoundResult:
        self.node_max_retry_times = 3
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('零号空洞-入口', '领取')

        result = self.round_by_ocr_and_click(screen, '领取', area=area,
                                             color_range=[(100, 100, 0), (255, 255, 20)])
        if result.is_success:
            time.sleep(1.5)
            self.round_by_click_area('菜单', '返回')
            return self.round_wait(wait=1)

        return self.round_retry(result.status, wait=1)

    @node_from(from_name='领取奖励')
    @node_from(from_name='领取奖励', success=False)
    @operation_node(name='完成')
    def finish(self) -> OperationRoundResult:
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op(op.execute())


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    op = HollowZeroApp(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()