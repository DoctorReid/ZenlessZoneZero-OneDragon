from one_dragon.base.operation.operation import Operation
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.base.operation.operation_node import OperationNode
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext


class OpenAndEnterGame(Operation):

    def __init__(self, ctx: ZContext):
        Operation.__init__(self, ctx, op_name=gt('打开并登录游戏', 'ui'),
                           need_check_game_win=False)

    def handle_init(self):
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        pass

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        open_game = OperationNode('打开游戏', self.open_game)
        enter_game = OperationNode('进入游戏', self.enter_game)
        self.add_edge(open_game, enter_game)

    def open_game(self) -> OperationRoundResult:
        """
        打开游戏
        :return:
        """
        return self.round_fail('未支持打开游戏')

    def enter_game(self) -> OperationRoundResult:
        """
        进入游戏
        :return:
        """
        return self.round_fail('未支持打开游戏')
