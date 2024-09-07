from typing import List, ClassVar

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroSpecialEvent
from zzz_od.hollow_zero.event import hollow_event_utils
from zzz_od.hollow_zero.event.event_ocr_result_handler import EventOcrResultHandler
from zzz_od.hollow_zero.hollow_battle import HollowBattle
from zzz_od.operation.zzz_operation import ZOperation


class CriticalStage(ZOperation):

    OPT_1: ClassVar[str] = '确认继续'

    def __init__(self, ctx: ZContext):
        """
        确定出现事件后调用
        :param ctx:
        """
        event_name = HollowZeroSpecialEvent.CRITICAL_STAGE.value.event_name
        ZOperation.__init__(
            self, ctx,
            op_name=gt(event_name)
        )

        self._handlers: List[EventOcrResultHandler] = [
            EventOcrResultHandler(CriticalStage.OPT_1, lcs_percent=1),
            EventOcrResultHandler(event_name, is_event_mark=True)
        ]

    @operation_node(name='画面识别', is_start_node=True)
    def check_screen(self) -> OperationRoundResult:
        screen = self.screenshot()
        return event_utils.check_event_text_and_run(self, screen, self._handlers)

    @node_from(from_name='画面识别', status=OPT_1)
    @operation_node(name='自动战斗')
    def load_auto_op(self) -> OperationRoundResult:
        op = HollowBattle(self.ctx, is_critical_stage=True)
        return self.round_by_op(op.execute())

    @node_from(from_name='自动战斗', status='普通战斗-完成')
    @operation_node(name='通关次数')
    def add_times(self) -> OperationRoundResult:
        self.ctx.hollow_zero_record.add_times()
        return self.round_success()
