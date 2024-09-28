from typing import List

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.arcade.arcade_snake_suicide import ArcadeSnakeSuicide
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.compendium.compendium_choose_tab import CompendiumChooseTab
from zzz_od.operation.compendium.open_compendium import OpenCompendium
from zzz_od.operation.eat_noodle import EatNoodle


class WeeklyScheduleApp(ZApplication):

    def __init__(self, ctx: ZContext):
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='weekly_schedule',
            op_name=gt('每周行程', 'ui'),
            run_record=ctx.weekly_schedule_record,
            retry_in_od=True,  # 传送落地有可能会歪 重试
        )
        self.to_choose_list: List[str] = ['前往电玩店玩2局游戏', '享用1碗拉面']
        self.to_choose_idx: int = 0

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        self.to_choose_idx: int = 0

    @operation_node(name='快捷手册', is_start_node=True)
    def open_compendium(self) -> OperationRoundResult:
        op = OpenCompendium(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='快捷手册')
    @operation_node(name='日常')
    def choose_train(self) -> OperationRoundResult:
        op = CompendiumChooseTab(self.ctx, '日常')
        return self.round_by_op_result(op.execute(), wait=1)

    @node_from(from_name='日常')
    @operation_node(name='行程安排')
    def click_schedule(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '每周行程', '行程安排',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='行程安排')
    @operation_node(name='选择代办')
    def choose_schedule(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('每周行程', '代办列表')

        if self.to_choose_idx >= len(self.to_choose_list):
            return self.round_success()

        target_cn = self.to_choose_list[self.to_choose_idx]
        result = self.round_by_ocr_and_click(screen, target_cn, area=area)
        if result.is_success:
            self.to_choose_idx += 1
            return self.round_wait(result.status, wait=1)

        start_point = area.center
        end_point = start_point + Point(0, -100)
        self.ctx.controller.drag_to(start=start_point, end=end_point)
        return self.round_retry(result.status, wait=0.5)

    @node_from(from_name='选择代办')
    @operation_node(name='确认代办')
    def confirm_schedule(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '每周行程', '确认代办',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='确认代办')
    @operation_node(name='拉面')
    def eat_noodle(self) -> OperationRoundResult:
        op = EatNoodle(self.ctx, '白碗草本汤面')
        return self.round_by_op_result(op.execute())

    @node_from(from_name='拉面')
    @operation_node(name='蛇对蛇')
    def snake(self) -> OperationRoundResult:
        op = ArcadeSnakeSuicide(self.ctx, 2)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='蛇对蛇')
    @operation_node(name='领奖励-快捷手册')
    def open_compendium_after(self) -> OperationRoundResult:
        op = OpenCompendium(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='领奖励-快捷手册')
    @operation_node(name='领奖励-日常')
    def choose_train_after(self) -> OperationRoundResult:
        op = CompendiumChooseTab(self.ctx, '日常')
        return self.round_by_op_result(op.execute(), wait=1)

    @node_from(from_name='领奖励-日常')
    @operation_node(name='点击领取')
    def click_reward(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '每周行程', '领取',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='点击领取')
    @operation_node(name='完成后返回')
    def finish(self) -> OperationRoundResult:
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op_result(op.execute())


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    app = WeeklyScheduleApp(ctx)
    app.execute()


if __name__ == '__main__':
    __debug()