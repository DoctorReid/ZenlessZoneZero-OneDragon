from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class ExitInBattle(ZOperation):

    def __init__(self, ctx: ZContext):
        """
        在战斗画面 尝试退出
        :param ctx: 上下文
        """
        ZOperation.__init__(self, ctx, op_name=gt('战斗中退出'))

        self.click_confirm: bool = False  # 已经点击了确认按钮

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
        result = self.round_by_find_area(screen, '恶名狩猎', '退出战斗')
        if result.is_success:
            return self.round_success(wait=1)  # 稍微等一下让按钮可按

        return self.round_retry(result.status, wait=1)

    @node_from(from_name='画面识别')
    @operation_node(name='点击退出战斗')
    def click_exit_battle(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_and_click_area(screen, '恶名狩猎', '退出战斗')
        if result.is_success:
            return self.round_wait(result.status, wait=1)

        result = self.round_by_find_and_click_area(screen, '恶名狩猎', '退出战斗-确认')
        if result.is_success:
            self.click_confirm = True
            return self.round_wait(result.status, wait=1)

        if self.click_confirm:
            return self.round_success()
        else:
            return self.round_retry(result.status, wait=1)
