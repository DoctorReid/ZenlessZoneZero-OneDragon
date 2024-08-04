from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.base.operation.operation_node import OperationNode
from one_dragon.base.screen.screen_utils import FindAreaResultEnum
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class BackToNormalWorld(ZOperation):

    def __init__(self, ctx: ZContext):
        """
        需要保证在任何情况下调用，都能返回大世界，让后续的应用可执行
        :param ctx:
        """
        ZOperation.__init__(self, ctx,
                            node_max_retry_times=5,
                            op_name=gt('返回大世界', 'ui')
                            )

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check = OperationNode('画面识别', self.check_screen_and_run)

        self.param_start_node = check

    def handle_init(self):
        pass

    def check_screen_and_run(self) -> OperationRoundResult:
        """
        识别游戏画面
        :return:
        """
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '大世界', '信息')

        if result.is_success:
            return self.round_success()

        result = self.round_by_find_area(screen, '快捷手册', 'TAB-挑战')

        if result.is_success:
            self.click_area('快捷手册', '退出')
            return self.round_retry(wait=1)

        click_back = self.click_area('菜单', '返回')
        if click_back:
            return self.round_retry(wait_round_time=1)
        else:
            return self.round_fail()
