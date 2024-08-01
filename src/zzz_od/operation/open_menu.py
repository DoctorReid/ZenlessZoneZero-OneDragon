from typing import ClassVar

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.zzz_operation import ZOperation


class OpenMenu(ZOperation):

    STATUS_NOT_IN_MENU: ClassVar[str] = '未在菜单页面'

    def __init__(self, ctx: ZContext):
        """
        识别画面 打开菜单
        由于使用了返回大世界 应可保证在任何情况下使用
        :param ctx:
        """
        ZOperation.__init__(self, ctx,
                            op_name=gt('打开菜单', 'ui')
                            )

    @node_from(from_name='点击菜单')
    @operation_node(name='画面识别', is_start_node=True)
    def check_menu(self) -> OperationRoundResult:
        """
        识别画面
        :return:
        """
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '菜单', '更多')
        if result.is_success:
            return self.round_success()
        else:
            return self.round_success(status=OpenMenu.STATUS_NOT_IN_MENU)

    @node_from(from_name='画面识别', status=STATUS_NOT_IN_MENU)
    @operation_node(name='返回大世界')
    def back_to_world(self) -> OperationRoundResult:
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op(op.execute())

    @node_from(from_name='返回大世界')
    @operation_node(name='点击菜单')
    def click_menu(self) -> OperationRoundResult:
        """
        在大世界画面 点击菜单的按钮
        :return:
        """
        click = self.click_area('大世界', '菜单')
        if click:
            return self.round_success(wait=2)
        else:
            return self.round_retry(wait=1)


if __name__ == '__main__':
    ctx = ZContext()
    op = OpenMenu(ctx)
    op._init_before_execute()
    pass