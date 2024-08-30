import subprocess

from one_dragon.base.operation.operation import Operation
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from zzz_od.context.zzz_context import ZContext


class OpenGame(Operation):

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx
        Operation.__init__(self, ctx, op_name=gt('打开游戏', 'ui'),
                           need_check_game_win=False)

    @operation_node(name='打开游戏', is_start_node=True)
    def open_game(self) -> OperationRoundResult:
        """
        打开游戏
        :return:
        """
        if self.ctx.game_config.game_path == '':
            return self.round_fail('未配置游戏路径')
        log.info('尝试自动启动游戏 路径为 %s', self.ctx.game_config.game_path)
        subprocess.Popen(
            f'cmd /c "start "" "{self.ctx.game_config.game_path}" & exit"'
        )
        return self.round_success(wait=5)
