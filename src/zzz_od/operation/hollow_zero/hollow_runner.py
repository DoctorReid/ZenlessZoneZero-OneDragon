import time

from cv2.typing import MatLike
from typing import Type

from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroSpecialEvent
from zzz_od.hollow_zero.hollow_map.hollow_zero_map import HollowZeroMapNode, HollowZeroMap
from zzz_od.operation.hollow_zero import hollow_utils
from zzz_od.operation.hollow_zero.event.bamboo_merchant import BambooMerchant
from zzz_od.operation.hollow_zero.event.call_for_support import CallForSupport
from zzz_od.operation.hollow_zero.event.choose_resonium import ChooseResonium
from zzz_od.operation.hollow_zero.event.confirm_resonium import ConfirmResonium
from zzz_od.operation.hollow_zero.event.critical_stage import CriticalStage
from zzz_od.operation.hollow_zero.event.drop_resonium import DropResonium
from zzz_od.operation.hollow_zero.event.normal_event_handler import NormalEventHandler
from zzz_od.operation.hollow_zero.event.remove_corruption import RemoveCorruption
from zzz_od.operation.hollow_zero.event.swift_supply import SwiftSupply
from zzz_od.operation.hollow_zero.event.switch_resonium import SwitchResonium
from zzz_od.operation.hollow_zero.event.upgrade_resonium import UpgradeResonium
from zzz_od.operation.hollow_zero.hollow_battle import HollowBattle
from zzz_od.operation.zzz_operation import ZOperation


class HollowRunner(ZOperation):

    def __init__(self, ctx: ZContext):
        ZOperation.__init__(
            self, ctx,
            node_max_retry_times=60,
            op_name=gt('空洞操作器')
        )

        self._special_event_handlers: dict[str, Type] = {
            HollowZeroSpecialEvent.CALL_FOR_SUPPORT.value.event_name: CallForSupport,

            HollowZeroSpecialEvent.RESONIUM_STORE_1.value.event_name: BambooMerchant,
            HollowZeroSpecialEvent.RESONIUM_STORE_2.value.event_name: BambooMerchant,
            HollowZeroSpecialEvent.RESONIUM_STORE_3.value.event_name: BambooMerchant,

            HollowZeroSpecialEvent.RESONIUM_CHOOSE.value.event_name: ChooseResonium,
            HollowZeroSpecialEvent.RESONIUM_CONFIRM_1.value.event_name: ConfirmResonium,
            HollowZeroSpecialEvent.RESONIUM_CONFIRM_2.value.event_name: ConfirmResonium,
            HollowZeroSpecialEvent.RESONIUM_UPGRADE.value.event_name: UpgradeResonium,
            HollowZeroSpecialEvent.RESONIUM_DROP.value.event_name: DropResonium,
            HollowZeroSpecialEvent.RESONIUM_SWITCH.value.event_name: SwitchResonium,
            HollowZeroSpecialEvent.SWIFT_SUPPLY_LIFE.value.event_name: SwiftSupply,
            HollowZeroSpecialEvent.SWIFT_SUPPLY_COIN.value.event_name: SwiftSupply,
            HollowZeroSpecialEvent.SWIFT_SUPPLY_PRESS.value.event_name: SwiftSupply,

            HollowZeroSpecialEvent.CORRUPTION_REMOVE.value.event_name: RemoveCorruption,

            HollowZeroSpecialEvent.CRITICAL_STAGE.value.event_name: CriticalStage,
            HollowZeroSpecialEvent.IN_BATTLE.value.event_name: HollowBattle,
        }
        self._last_save_image_time: float = 0

    @operation_node(name='画面识别', is_start_node=True)
    def check_screen(self) -> OperationRoundResult:
        now = time.time()
        screen = self.screenshot()
        result = hollow_utils.check_screen(self, screen)
        if result is not None:
            return self._handle_event(screen, result)

        # 当前识别到地图
        current_map = self.ctx.hollow.check_current_map(screen, now)
        if current_map is not None and current_map.current_idx is not None:
            self.ctx.hollow.check_before_move(screen)
            return self._handle_map_move(screen, current_map)

        self.round_by_click_area('零号空洞-事件', '空白')
        return self.round_retry('未能识别当前画面', wait=1)

    def _handle_event(self, screen: MatLike, event_name: str) -> OperationRoundResult:
        """
        识别到事件时 进行处理
        :param event_name:
        :return:
        """
        normal_event = self.ctx.hollow.data_service.get_normal_event_by_name(event_name=event_name)
        if normal_event is not None:
            op = NormalEventHandler(self.ctx, normal_event)
            op_result = op.execute()
            if op_result.success:
                return self.round_wait()
            else:
                return self.round_retry(wait=1)

        if event_name in self._special_event_handlers:
            op: ZOperation = self._special_event_handlers[event_name](self.ctx)
            op_result = op.execute()
            if op_result.success:
                return self.round_wait()
            else:
                return self.round_retry(wait=1)

        if event_name == HollowZeroSpecialEvent.MISSION_COMPLETE.value.event_name:
            return self.round_by_find_and_click_area(screen, '零号空洞-事件', '通关-完成',
                                                     success_wait=5, retry_wait=1)

        return self.round_retry('当前事件未有对应指令', wait=1)

    def _handle_map_move(self, screen: MatLike, current_map: HollowZeroMap) -> OperationRoundResult:
        """
        识别到地图后 自动寻路
        :param current_map:
        :return:
        """
        next_to_move: HollowZeroMapNode = self.ctx.hollow.get_next_to_move(current_map)
        if next_to_move is None:
            self._save_debug_image(screen)
            return self.round_retry('自动寻路失败')

        self.ctx.controller.click(next_to_move.pos.center)
        self.ctx.hollow.update_context_after_move(next_to_move)

        return self.round_wait(wait=1)

    def _save_debug_image(self, screen: MatLike) -> None:
        """
        保存图片用于优化模型
        """
        if not self.ctx.env_config.is_debug:
            return
        now = time.time()
        if now - self._last_save_image_time < 1:
            return
        self._last_save_image_time = now
        from one_dragon.utils import debug_utils
        debug_utils.save_debug_image(screen, prefix='pathfinding_fail')


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.start_running()
    ctx.ocr.init_model()
    ctx.hollow.init_event_yolo(True)
    op = HollowRunner(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()