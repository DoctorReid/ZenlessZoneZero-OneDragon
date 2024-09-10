from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class Deploy(ZOperation):

    def __init__(self, ctx: ZContext):
        """
        在出战页面 点击出战
        同时处理可能出现的对话框
        :param ctx:
        """
        ZOperation.__init__(self, ctx, op_name=gt('出战', 'ui'))

    def handle_init(self):
        pass

    @operation_node(name='出战', is_start_node=True)
    def deploy(self) -> OperationRoundResult:
        screen = self.screenshot()

        return self.round_by_find_and_click_area(
            screen, '实战模拟室', '出战',
            success_wait=1, retry_wait=1
        )

    @node_from(from_name='出战')
    @operation_node(name='识别低等级')
    def check_level(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '实战模拟室', '确定并出战',
                                                 retry_wait=1)

    @node_from(from_name='识别低等级')
    @node_from(from_name='识别低等级', success=False)
    @operation_node(name='进入成功')
    def finish(self) -> OperationRoundResult:
        return self.round_success()
