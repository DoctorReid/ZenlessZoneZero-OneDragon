import os
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
        full_path = self.ctx.game_config.game_path
        log.info('尝试自动启动游戏 路径为 %s', full_path)
        # 获取文件夹路径
        dir_path = os.path.dirname(full_path)
        exe_name = os.path.basename(full_path)
        command = f'cmd /c "start "" "{dir_path}\{exe_name}"'
        if self.ctx.game_config.launch_arguement:
            screen_size = self.ctx.game_config.screen_size
            screen_width = screen_size.split('x')[0]
            screen_height = screen_size.split('x')[1]
            full_screen = self.ctx.game_config.full_screen
            monitor = self.ctx.game_config.monitor
            arguement = f'{self.ctx.game_config.launch_arguement_advance} -screen-width {screen_width} -screen-height {screen_height} -screen-fullscreen {full_screen} -monitor {monitor}' 
            command = f'{command} {arguement}'
        command = f'{command} & exit"'
        log.info('命令行指令 %s', command)
        subprocess.Popen(command)
        return self.round_success(wait=5)
