from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class ExitInBattle(ZOperation):

    def __init__(self, ctx: ZContext, wait_screen_name: str = None, wait_area_name: str = None):
        """
        在战斗画面 尝试退出
        :param ctx: 上下文
        """
        ZOperation.__init__(self, ctx, op_name=gt('战斗中退出'))

        self.wait_screen_name: str = wait_screen_name  # 退出后等待的画面名称
        self.wait_area_name: str = wait_area_name  # 退出后等待的画面名称

    @operation_node(name='画面识别', is_start_node=True, node_max_retry_times=10)
    def check_screen(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '战斗画面', '按键-普通攻击')
        if result.is_success:
            result2 = self.round_by_click_area('战斗画面', '菜单')
            if result2.is_success:
                return self.round_wait(result2.status, wait=1)
            else:
                return self.round_retry(result2.status, wait=1)

        # 点击直到出现 [退出战斗] 按钮
        result = self.round_by_find_area(screen, '战斗-菜单', '按钮-退出战斗')
        if result.is_success:
            return self.round_success(wait=1)  # 稍微等一下让按钮可按

        return self.round_retry(result.status, wait=1)

    @node_from(from_name='画面识别')
    @operation_node(name='点击退出战斗')
    def click_exit_battle(self) -> OperationRoundResult:
        screen = self.screenshot()

        return self.round_by_find_and_click_area(screen, '战斗-菜单', '按钮-退出战斗',
                                                 until_find_all=[('战斗-菜单', '按钮-退出战斗-确认')],
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='点击退出战斗')
    @operation_node(name='点击确认')
    def click_confirm(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='战斗-菜单', area_name='按钮-退出战斗-确认',
                                                 until_not_find_all=[('战斗-菜单', '按钮-退出战斗-确认')],
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='点击确认')
    @operation_node(name='退出后等待', node_max_retry_times=60)
    def wait_at_last(self) -> OperationRoundResult:
        if self.wait_screen_name is None or self.wait_area_name is None:
            return self.round_success()
        screen = self.screenshot()
        return self.round_by_find_area(screen, self.wait_screen_name, self.wait_area_name,
                                       retry_wait=1)