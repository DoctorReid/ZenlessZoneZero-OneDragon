from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.open_menu import OpenMenu


class CityFundApp(ZApplication):

    def __init__(self, ctx: ZContext):
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='city_fund',
            op_name=gt('丽都城募', 'ui'),
            run_record=ctx.city_fund_record
        )

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        pass

    @operation_node(name='打开菜单', is_start_node=True)
    def open_menu(self) -> OperationRoundResult:
        op = OpenMenu(self.ctx)
        return self.round_by_op(op.execute())

    @node_from(from_name='打开菜单')
    @operation_node(name='点击丽都城募')
    def click_fund(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('菜单', '底部列表')
        return self.round_by_ocr_and_click(screen, '丽都城募', area=area,
                                           success_wait=1, retry_wait=1)

    @node_from(from_name='点击丽都城募')
    @operation_node(name='点击成长任务')
    def click_task(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '丽都城募', '成长任务',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='点击成长任务')
    @operation_node(name='任务全部领取')
    def click_task_claim(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '丽都城募', '任务-全部领取',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='任务全部领取')
    @operation_node(name='点击等级回馈')
    def click_level(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '丽都城募', '等级回馈',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='点击等级回馈')
    @operation_node(name='等级全部领取')
    def click_level_claim(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '丽都城募', '等级-全部领取',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='等级全部领取')
    @node_from(from_name='等级全部领取', success=False)
    @operation_node(name='返回大世界')
    def back_to_world(self) -> OperationRoundResult:
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op(op.execute())


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    app = CityFundApp(ctx)
    app.execute()


if __name__ == '__main__':
    __debug()