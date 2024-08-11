from typing import Type

from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.hollow_zero import hollow_utils
from zzz_od.operation.hollow_zero.event.call_for_support import CallForSupport
from zzz_od.operation.hollow_zero.event.choose_resonium import ChooseResonium
from zzz_od.operation.hollow_zero.event.confirm_resonium import ConfirmResonium
from zzz_od.operation.hollow_zero.event.critical_stage import CriticalStage
from zzz_od.operation.hollow_zero.event.normal_event_handler import NormalEventHandler
from zzz_od.operation.hollow_zero.event.swift_supply import SwiftSupply
from zzz_od.operation.hollow_zero.event.remove_corruption import RemoveCorruption
from zzz_od.operation.hollow_zero.event.resonium_store import ResoniumStore
from zzz_od.operation.hollow_zero.event.upgrade_resonium import UpgradeResonium
from zzz_od.operation.hollow_zero.hollow_battle import HollowBattle
from zzz_od.operation.hollow_zero.hollow_zero_event import HollowZeroSpecialEvent
from zzz_od.operation.zzz_operation import ZOperation


class HollowRunner(ZOperation):

    def __init__(self, ctx: ZContext):
        ZOperation.__init__(
            self, ctx,
            node_max_retry_times=20,
            op_name=gt('空洞操作器')
        )

        self._special_event_handlers: dict[str, Type] = {
            HollowZeroSpecialEvent.CALL_FOR_SUPPORT.value.event_name: CallForSupport,

            HollowZeroSpecialEvent.RESONIUM_STORE.value.event_name: ResoniumStore,

            HollowZeroSpecialEvent.RESONIUM_CHOOSE.value.event_name: ChooseResonium,
            HollowZeroSpecialEvent.RESONIUM_CONFIRM_1.value.event_name: ConfirmResonium,
            HollowZeroSpecialEvent.RESONIUM_CONFIRM_2.value.event_name: ConfirmResonium,
            HollowZeroSpecialEvent.RESONIUM_UPGRADE.value.event_name: UpgradeResonium,
            HollowZeroSpecialEvent.SWIFT_SUPPLY_LIFE.value.event_name: SwiftSupply,
            HollowZeroSpecialEvent.SWIFT_SUPPLY_COIN.value.event_name: SwiftSupply,
            HollowZeroSpecialEvent.SWIFT_SUPPLY_PRESS.value.event_name: SwiftSupply,

            HollowZeroSpecialEvent.CORRUPTION_REMOVE.value.event_name: RemoveCorruption,

            HollowZeroSpecialEvent.CRITICAL_STAGE.value.event_name: CriticalStage,
            HollowZeroSpecialEvent.IN_BATTLE.value.event_name: HollowBattle,
        }

    @operation_node(name='画面识别', is_start_node=True)
    def check_screen(self) -> OperationRoundResult:
        screen = self.screenshot()
        result = hollow_utils.check_screen(self, screen)
        if result is None:
            self.round_by_click_area('零号空洞-事件', '空白')
            return self.round_retry('未能识别当前画面', wait=1)

        normal_event = self.ctx.hollow.event_service.get_normal_event_by_name(event_name=result)
        if normal_event is not None:
            op = NormalEventHandler(self.ctx, normal_event)
            op_result = op.execute()
            if op_result.success:
                return self.round_wait()
            else:
                return self.round_retry(wait=1)

        if result in self._special_event_handlers:
            op: ZOperation = self._special_event_handlers[result](self.ctx)
            op_result = op.execute()
            if op_result.success:
                return self.round_wait()
            else:
                return self.round_retry(wait=1)

        if result == HollowZeroSpecialEvent.MISSION_COMPLETE.value.event_name:
            return self.round_by_find_and_click_area(screen, '零号空洞-事件', '通关-完成',
                                                     success_wait=5, retry_wait=1)

        return self.round_retry('当前画面未有对应指令', wait=1)


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.start_running()
    ctx.ocr.init_model()
    op = HollowRunner(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()