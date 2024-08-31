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
from one_dragon.utils.log_utils import log
from zzz_od.operation.hollow_zero.event.event_ocr_result_handler import EventOcrResultHandler
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroSpecialEvent, HallowZeroEvent
from zzz_od.operation.zzz_operation import ZOperation


def check_event_at_right(op: ZOperation, screen: MatLike) -> Optional[str]:
    """
    识别右边区域 当前是什么事件
    """
    area = get_event_text_area(op)
    part = cv2_utils.crop_image_only(screen, area.rect)
    white = cv2.inRange(part, (240, 240, 240), (255, 255, 255))
    white = cv2_utils.dilate(white, 5)
    to_ocr = cv2.bitwise_and(part, part, mask=white)
    ocr_result_map = op.ctx.ocr.run_ocr(to_ocr)

    event_name_list = []
    event_name_gt_list = []
    for event in op.ctx.hollow.data_service.normal_events:
        event_name_list.append(event.event_name)
        event_name_gt_list.append(gt(event.event_name))

    for event_enum in HollowZeroSpecialEvent:
        event = event_enum.value
        if not event.on_the_right:
            continue
        event_name_list.append(event.event_name)
        event_name_gt_list.append(gt(event.event_name))

    # 事件标题一定在最上方 因此找y最小的
    min_y = 9999
    for ocr_result, mrl in ocr_result_map.items():
        if mrl.max.y < min_y:
            min_y = mrl.max.y

    ocr_result_list = []
    for ocr_result, mrl in ocr_result_map.items():
        if mrl.max.y - min_y < 20:
            ocr_result_list.append(ocr_result)

    event_idx, _ = str_utils.find_most_similar(event_name_gt_list, ocr_result_list)

    if event_idx is not None:
        return event_name_list[event_idx]


def check_event_text_and_run(op: ZOperation, screen: MatLike, handlers: List[EventOcrResultHandler]) -> OperationRoundResult:
    """
    识别当前事件的文本 并做出选择
    """
    area = get_event_text_area(op)
    part = cv2_utils.crop_image_only(screen, area.rect)
    white = cv2.inRange(part, (240, 240, 240), (255, 255, 255))
    white = cv2_utils.dilate(white, 5)
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

    handler_str_list = [gt(handler.target_cn) for handler in handlers]

    # 由于选项和识别的文本都是多个，多对多的情况下需要双向匹配才算成功匹配
    for handler in handlers:
        handler_event_str = gt(handler.target_cn)
        results = difflib.get_close_matches(handler_event_str, ocr_result_list, n=1)

        if results is None or len(results) == 0:
            continue

        ocr_result = results[0]
        # 同时需要反向匹配到一样的
        results2 = difflib.get_close_matches(ocr_result, handler_str_list, n=1)
        if results2 is None or len(results2) == 0 or results2[0] != handler_event_str:
            continue

        ocr_result_idx = ocr_result_list.index(ocr_result)
        mrl = mrl_list[ocr_result_idx]

        if handler.is_event_mark:
            if event_mark_handler is None:
                event_mark_handler = handler
                event_mark_mrl = mrl
        elif target_handler is None:
            target_handler = handler
            target_mrl = mrl

    if target_handler is not None:
        log.debug('识别事件选项 %s' % target_handler.target_cn)
        return run_event_handler(op, target_handler, area, target_mrl.max)
    elif event_mark_handler is not None:
        log.debug('识别事件无选项 %s' % event_mark_handler.target_cn)
        return click_empty(op)
    else:
        click_empty(op)  # 做一个兜底点击 感觉可以跟上面合并
        return op.round_retry('未匹配合适的处理方法', wait=1)


def click_empty(op: ZOperation) -> OperationRoundResult:
    return op.round_by_click_area('零号空洞-事件', '事件文本', click_left_top=True,
                                  success_wait=0.2, retry_wait=0.2)


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
    底部是否有 选择、确认、催化、丢弃、交换、抵押欠款
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
        HollowZeroSpecialEvent.RESONIUM_DROP.value,
        HollowZeroSpecialEvent.RESONIUM_DROP_2.value,
        HollowZeroSpecialEvent.RESONIUM_SWITCH.value,
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
