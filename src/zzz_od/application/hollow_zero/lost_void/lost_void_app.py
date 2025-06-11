from typing import ClassVar

from one_dragon.base.operation.operation import Operation
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.log_utils import log
from zzz_od.application.hollow_zero.lost_void.lost_void_challenge_config import LostVoidRegionType
from zzz_od.application.hollow_zero.lost_void.operation.lost_void_run_level import LostVoidRunLevel
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.compendium import CompendiumMissionType
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.compendium.compendium_choose_category import CompendiumChooseCategory
from zzz_od.operation.compendium.compendium_choose_mission_type import CompendiumChooseMissionType
from zzz_od.operation.deploy import Deploy


class LostVoidApp(ZApplication):

    STATUS_ENOUGH_TIMES: ClassVar[str] = '完成通关次数'
    STATUS_AGAIN: ClassVar[str] = '继续挑战'

    def __init__(self, ctx: ZContext):
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='lost_void',
            op_name='迷失之地',
            run_record=ctx.lost_void_record,
            need_notify=True,
        )

        self.next_region_type: LostVoidRegionType = LostVoidRegionType.ENTRY  # 下一个区域的类型

    @operation_node(name='初始化加载', is_start_node=True)
    def init_for_lost_void(self) -> OperationRoundResult:
        if self.ctx.lost_void_record.is_finished_by_day():
            return self.round_success(LostVoidApp.STATUS_ENOUGH_TIMES)

        try:
            # 这里会加载迷失之洞的数据 识别模型 和自动战斗配置
            self.ctx.lost_void.init_before_run()
        except Exception:
            return self.round_fail('初始化失败')
        return self.round_success(LostVoidApp.STATUS_AGAIN)

    @node_from(from_name='初始化加载', status=STATUS_AGAIN)
    @operation_node(name='识别初始画面')
    def check_initial_screen(self) -> OperationRoundResult:
        screen = self.screenshot()

        # 特殊兼容 在挑战区域开始
        result = self.round_by_find_and_click_area(screen, '迷失之地-大世界', '按钮-挑战-确认')
        if result.is_success:
            self.next_region_type = LostVoidRegionType.CHANLLENGE_TIME_TRAIL
            return self.round_wait(result.status, wait=1)

        screen_name, can_go = self.check_screen_with_can_go(screen, '迷失之地-战线肃清')
        if screen_name is None:
            return self.round_retry(Operation.STATUS_SCREEN_UNKNOWN, wait=0.5)

        if screen_name == '迷失之地-大世界':
            return self.round_success('迷失之地-大世界')

        if can_go or screen_name == '迷失之地-战线肃清':
            return self.round_success('可前往战线肃清')

        can_go = self.check_current_can_go('快捷手册-作战')
        if can_go:
            return self.round_success('可前往快捷手册')

        return self.round_retry('无法前往目标画面', wait=0.5)

    @node_from(from_name='识别初始画面', status=Operation.STATUS_SCREEN_UNKNOWN)
    @node_from(from_name='识别初始画面', status='无法前往目标画面')
    @operation_node(name='开始前返回大世界')
    def back_at_first(self) -> OperationRoundResult:
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='识别初始画面', status='可前往快捷手册')
    @node_from(from_name='开始前返回大世界')
    @operation_node(name='前往快捷手册')
    def goto_compendium(self) -> OperationRoundResult:
        return self.round_by_goto_screen(screen_name='快捷手册-作战')

    @node_from(from_name='前往快捷手册')
    @operation_node(name='选择零号空洞')
    def choose_hollow_zero(self) -> OperationRoundResult:
        op = CompendiumChooseCategory(self.ctx, '零号空洞')
        return self.round_by_op_result(op.execute())

    @node_from(from_name='选择零号空洞')
    @operation_node(name='选择迷失之地')
    def choose_lost_void(self) -> OperationRoundResult:
        mission_type: CompendiumMissionType = self.ctx.compendium_service.get_mission_type_data('作战', '零号空洞', '迷失之地')
        op = CompendiumChooseMissionType(self.ctx, mission_type)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='识别初始画面', status='可前往战线肃清')
    @node_from(from_name='选择迷失之地')
    @node_from(from_name='通关后处理', status=STATUS_AGAIN)
    @operation_node(name='前往战线肃清', node_max_retry_times=60)
    def goto_purge(self) -> OperationRoundResult:
        return self.round_by_goto_screen(screen_name='迷失之地-战线肃清')

    @node_from(from_name='前往战线肃清')
    @operation_node(name='选择增益')
    def choose_buff(self) -> OperationRoundResult:
        return self.round_by_click_area('迷失之地-战线肃清', f'周期增益-{self.ctx.lost_void.challenge_config.period_buff_no}',
                                        success_wait=1, retry_wait=1)

    @node_from(from_name='选择增益')
    @operation_node(name='下一步')
    def click_next(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='通用-出战', area_name='按钮-下一步',
                                                 until_find_all=[('通用-出战', '按钮-出战')],
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='下一步')
    @operation_node(name='出战')
    def deploy(self) -> OperationRoundResult:
        self.next_region_type = LostVoidRegionType.ENTRY
        op = Deploy(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='识别初始画面', status='迷失之地-大世界')
    @node_from(from_name='出战')
    @node_from(from_name='层间移动')
    @operation_node(name='层间移动')
    def run_level(self) -> OperationRoundResult:
        log.info(f'推测楼层类型 {self.next_region_type.value.value}')
        op = LostVoidRunLevel(self.ctx, self.next_region_type)
        op_result = op.execute()
        if op_result.success:
            if op_result.status == LostVoidRunLevel.STATUS_NEXT_LEVEL:
                if op_result.data is not None:
                    self.next_region_type = LostVoidRegionType.from_value(op_result.data)
                else:
                    self.next_region_type = LostVoidRegionType.ENTRY

        return self.round_by_op_result(op_result)

    @node_from(from_name='层间移动', status=LostVoidRunLevel.STATUS_COMPLETE)
    @operation_node(name='通关后处理', node_max_retry_times=60)
    def after_complete(self) -> OperationRoundResult:
        screen = self.screenshot()
        screen_name = self.check_and_update_current_screen(screen)
        if screen_name != '迷失之地-入口':
            return self.round_retry('等待画面加载')

        self.ctx.lost_void_record.add_complete_times()

        if self.ctx.lost_void_record.is_finished_by_day():
            return self.round_success(LostVoidApp.STATUS_ENOUGH_TIMES)

        return self.round_success(LostVoidApp.STATUS_AGAIN)

    @node_from(from_name='通关后处理')
    @operation_node(name='打开悬赏委托')
    def open_reward_list(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='迷失之地-入口', area_name='按钮-悬赏委托',
                                                 until_not_find_all=[('迷失之地-入口', '按钮-悬赏委托')],
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='打开悬赏委托')
    @operation_node(name='全部领取')
    def claim_all(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='迷失之地-入口', area_name='按钮-悬赏委托-全部领取',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='全部领取')
    @operation_node(name='完成后返回')
    def back_at_last(self) -> OperationRoundResult:
        self.notify_screenshot = self.save_screenshot_bytes()  # 结束后通知的截图
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op_result(op.execute())


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    op = LostVoidApp(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()
