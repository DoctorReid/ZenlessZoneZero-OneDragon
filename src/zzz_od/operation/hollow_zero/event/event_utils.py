import time

import cv2
import difflib
from cv2.typing import MatLike
from typing import Optional, List

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.operation.hollow_zero.event.event_ocr_result_handler import EventOcrResultHandler
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroSpecialEvent, HallowZeroEvent
from zzz_od.operation.zzz_operation import ZOperation


def check_event_at_right(op: ZOperation, screen: MatLike) -> Optional[str]:
    """
    识别右边区域 当前是什么事件
    """
    area = get_event_text_area(op)
    part = cv2_utils.crop_image_only(screen, area.rect)
    ocr_result_map = op.ctx.ocr.run_ocr(part)

    events: List[HallowZeroEvent] = [] + op.ctx.hollow.data_service.normal_events

    for event_enum in HollowZeroSpecialEvent:
        event = event_enum.value
        if event.on_the_right:
            events.append(event)

    for ocr_result in ocr_result_map.keys():
        for event in events:
            if str_utils.find_by_lcs(gt(event.event_name), ocr_result, percent=event.lcs_percent):
                return event.event_name


def check_event_text_and_run(op: ZOperation, screen: MatLike, handlers: List[EventOcrResultHandler]) -> OperationRoundResult:
    """
    识别当前事件的文本 并做出选择
    """
    area = get_event_text_area(op)
    part = cv2_utils.crop_image_only(screen, area.rect)
    white = cv2.inRange(part, (240, 240, 240), (255, 255, 255))
    to_ocr = cv2.bitwise_and(part, part, mask=white)

    ocr_result_map = op.ctx.ocr.run_ocr(to_ocr)

    target_handler: Optional[EventOcrResultHandler] = None
    target_mrl: Optional[MatchResultList] = None

    event_mark_handler: Optional[EventOcrResultHandler] = None
    event_mark_mrl: Optional[MatchResultList] = None

    ocr_result_list: List[str] = []
    mrl_list: List[MatchResultList] = []
    for ocr_result, mrl in ocr_result_map.items():
        ocr_result_list.append(ocr_result)
        mrl_list.append(mrl)

    for handler in handlers:
        results = difflib.get_close_matches(gt(handler.target_cn), ocr_result_list, n=1)

        if results is None or len(results) == 0:
            continue

        idx = ocr_result_list.index(results[0])
        ocr_result = ocr_result_list[idx]
        mrl = mrl_list[idx]
        if not str_utils.find_by_lcs(gt(handler.target_cn), ocr_result, percent=handler.lcs_percent):
            continue

        if handler.is_event_mark:
            if event_mark_handler is None:
                event_mark_handler = handler
                event_mark_mrl = mrl
        elif target_handler is None:
            target_handler = handler
            target_mrl = mrl

    if target_handler is not None:
        return run_event_handler(op, target_handler, area, target_mrl.max)
    elif event_mark_handler is not None:
        return click_empty(op)
    else:
        return op.round_retry('未匹配合适的处理方法', wait=1)


def click_empty(op: ZOperation) -> OperationRoundResult:
    return op.round_by_click_area('零号空洞-事件', '事件文本', click_left_top=True,
                                  success_wait=1, retry_wait=1)


def click_rect(op: ZOperation, status: str, rect: Rect, wait: float = 1) -> OperationRoundResult:
    """
    点击一个位置
    """
    click = op.ctx.controller.click(rect.center)
    if click:
        time.sleep(0.1)
        click_empty(op)
        return op.round_success(status, wait=wait)
    else:
        return op.round_retry(f'点击失败 {status}', wait=1)


def get_event_text_area(op: ZOperation) -> ScreenArea:
    """
    获取事件文本区域
    """
    return op.ctx.screen_loader.get_area('零号空洞-事件', '事件文本')


def run_event_handler(op: ZOperation, handler: EventOcrResultHandler, area: ScreenArea, mr: MatchResult) -> OperationRoundResult:
    lt: Point = mr.left_top + area.left_top
    rb: Point = mr.right_bottom + area.left_top
    rect = Rect(lt.x, lt.y, rb.x, rb.y)

    if handler.method is None:
        if handler.click_result:
            return click_rect(op, handler.status, rect, wait=handler.click_wait)
    else:
        return handler.method(handler.target_cn, rect)

    return op.round_retry(f'未配置应对方法 {handler.status}', wait=1)


def check_dialog_confirm(op: ZOperation, screen: MatLike) -> Optional[str]:
    """
    是有有对话框的确认
    """
    result = op.round_by_find_area(screen, '零号空洞-事件', '消息-确认')
    if result.is_success:
        return result.status
    else:
        return None


def check_bottom_choose(op: ZOperation, screen: MatLike) -> Optional[str]:
    """
    底部是否有 选择、确认、催化
    - 鸣徽选择、催化
    - 奖励确认
    - 邦布选择
    """
    area = op.ctx.screen_loader.get_area('零号空洞-事件', '底部-选择列表')
    part = cv2_utils.crop_image_only(screen, area.rect)
    ocr_result_map = op.ctx.ocr.run_ocr(part)

    event_list = [
        HollowZeroSpecialEvent.RESONIUM_CHOOSE.value,
        HollowZeroSpecialEvent.RESONIUM_CONFIRM_1.value,
        HollowZeroSpecialEvent.RESONIUM_CONFIRM_2.value,
        HollowZeroSpecialEvent.RESONIUM_UPGRADE.value,
        HollowZeroSpecialEvent.SWIFT_SUPPLY_LIFE.value,
        HollowZeroSpecialEvent.SWIFT_SUPPLY_COIN.value,
        HollowZeroSpecialEvent.SWIFT_SUPPLY_PRESS.value
    ]

    for event in event_list:
        for ocr_result in ocr_result_map.keys():
            if str_utils.find_by_lcs(gt(event.event_name), ocr_result, percent=event.lcs_percent):
                return event.event_name


def check_bottom_remove(op: ZOperation, screen: MatLike) -> Optional[str]:
    """
    底部是否有 清除
    - 侵蚀症状
    """
    area = op.ctx.screen_loader.get_area('零号空洞-事件', '底部-清除列表')
    part = cv2_utils.crop_image_only(screen, area.rect)
    ocr_result_map = op.ctx.ocr.run_ocr(part)

    event = HollowZeroSpecialEvent.CORRUPTION_REMOVE.value
    for ocr_result in ocr_result_map.keys():
        if str_utils.find_by_lcs(gt(event.event_name), ocr_result, percent=event.lcs_percent):
            return event.event_name
