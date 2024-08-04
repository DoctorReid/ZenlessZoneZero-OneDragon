import time

from typing import ClassVar

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.transport import Transport
from zzz_od.operation.wait_normal_world import WaitNormalWorld


class ScratchCardApp(ZApplication):

    STATUS_ALL_VIDEO_CHOOSE: ClassVar[str] = '已选择全部录像带'

    def __init__(self, ctx: ZContext):
        """
        每天自动接收邮件奖励
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='scratch_card',
            node_max_retry_times=10,
            op_name=gt('刮刮卡', 'ui'),
            run_record=ctx.scratch_card_run_record
        )

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        pass

    @operation_node(name='传送', is_start_node=True)
    def transport(self) -> OperationRoundResult:
        op = Transport(self.ctx, '六分街', '报刊亭')
        return self.round_by_op(op.execute())

    @node_from(from_name='传送')
    @operation_node(name='等待加载')
    def wait_world(self) -> OperationRoundResult:
        op = WaitNormalWorld(self.ctx)
        return self.round_by_op(op.execute())

    @node_from(from_name='等待加载')
    @operation_node(name='移动交互')
    def move_and_interact(self) -> OperationRoundResult:
        """
        传送之后 往前移动一下 方便交互
        :return:
        """
        self.ctx.controller.move_w(press=True, press_time=1, release=True)
        time.sleep(1)

        self.ctx.controller.interact(press=True, press_time=0.2, release=True)
        time.sleep(3)

        return self.round_success()

    @node_from(from_name='移动交互')
    @operation_node(name='点击刮刮卡')
    def click_scratch_card(self) -> OperationRoundResult:
        screen = self.screenshot()

        return self.round_by_find_and_click_area(screen, '报刊亭', '刮刮卡',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='点击刮刮卡')
    @operation_node(name='刮刮')
    def scratch(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '报刊亭', '每日可刮取一次')
        if not result.is_success:
            return self.round_retry(status=result.status, wait=1)

        areas = [
            self.ctx.screen_loader.get_area('报刊亭', '刮层-%d' % i)
            for i in range(1, 4)
        ]

        for area in areas:
            start = area.rect.left_top
            end = area.rect.right_bottom
            self.ctx.controller.drag_to(start=start, end=end, duration=1.5)
            time.sleep(1)

        return self.round_success()

    @node_from(from_name='刮刮')
    @operation_node(name='返回大世界')
    def back_to_world(self) -> OperationRoundResult:
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op(op.execute())


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    app = ScratchCardApp(ctx)
    app.execute()


if __name__ == '__main__':
    __debug()