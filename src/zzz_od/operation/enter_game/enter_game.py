import time

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.zzz_operation import ZOperation


class EnterGame(ZOperation):

    def __init__(self, ctx: ZContext):
        ZOperation.__init__(self, ctx,
                            op_name=gt('进入游戏', 'ui')
                            )

    @node_from(from_name='输入账号密码')
    @operation_node(name='画面识别', is_start_node=True, node_max_retry_times=60)
    def check_screen(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_and_click_area(screen, '打开游戏', '点击进入游戏')
        if result.is_success:
            return self.round_success(result.status, wait=5)

        result = self.round_by_find_and_click_area(screen, '打开游戏', '账号密码')
        if result.is_success:
            return self.round_success(result.status, wait=1)

        return self.round_retry(wait=1)

    @node_from(from_name='画面识别', status='账号密码')
    @operation_node(name='输入账号密码')
    def input_account_password(self) -> OperationRoundResult:
        if self.ctx.game_config.account == '' or self.ctx.game_config.password == '':
            return self.round_fail('未配置账号密码')

        self.click_area('打开游戏', '账号输入区域')
        time.sleep(0.5)
        self.ctx.controller.keyboard_controller.keyboard.type(self.ctx.game_config.account)
        time.sleep(1.5)

        self.click_area('打开游戏', '密码输入区域')
        time.sleep(0.5)
        self.ctx.controller.keyboard_controller.keyboard.type(self.ctx.game_config.password)
        time.sleep(1.5)

        self.click_area('打开游戏', '同意按钮')
        time.sleep(0.5)

        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '打开游戏', '账号密码进入游戏',
                                                 success_wait=5, retry_wait=1)

    @node_from(from_name='画面识别', status='点击进入游戏')
    @operation_node(name='等待画面加载')
    def wait_game(self) -> OperationRoundResult:
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op(op.execute())


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.start_running()
    ctx.ocr.init_model()
    op = EnterGame(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()
