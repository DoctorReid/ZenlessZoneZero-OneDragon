import time

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class LostVoidChooseNoNum(ZOperation):

    def __init__(self, ctx: ZContext):
        """
        有详情 没有显示选择数量的选择
        :param ctx:
        """
        ZOperation.__init__(self, ctx, op_name='迷失之地-无数量选择')

    @operation_node(name='选择', is_start_node=True)
    def choose_artifact(self) -> OperationRoundResult:
        area = self.ctx.screen_loader.get_area('迷失之地-通用选择', '文本-详情')
        self.ctx.controller.mouse_move(area.center + Point(0, 100))
        time.sleep(0.1)
        screen = self.screenshot()

        screen_name = self.check_and_update_current_screen()
        if screen_name != '迷失之地-无数量选择':
            # 进入本指令之前 有可能识别错画面
            return self.round_retry(status=f'当前画面 {screen_name}', wait=1)

        # 没有数量显示 就是不需要选择 直接点击确定
        return self.round_by_find_and_click_area(screen, screen_name='迷失之地-无数量选择', area_name='按钮-确定',
                                                 success_wait=1, retry_wait=1)

def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.init_ocr()
    ctx.lost_void.init_before_run()
    ctx.start_running()

    op = LostVoidChooseNoNum(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()