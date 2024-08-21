from cv2.typing import MatLike
from typing import Optional

from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroSpecialEvent
from zzz_od.operation.hollow_zero.event import event_utils
from zzz_od.operation.zzz_operation import ZOperation


def check_screen(op: ZOperation, screen: MatLike) -> Optional[str]:
    """
    识别当前画面的状态
    """
    choose = event_utils.check_bottom_choose(op, screen)
    if choose is not None:
        return choose

    event = event_utils.check_event_at_right(op, screen)
    if event is not None:
        return event

    # 不同的消息框高度不一样 很难捕捉到确定的按钮
    # confirm = event_utils.check_dialog_confirm(op, screen)
    # if confirm is not None:
    #     return confirm

    remove = event_utils.check_bottom_remove(op, screen)
    if remove is not None:
        return remove

    battle = check_battle_screen(op, screen)
    if battle is not None:
        return battle

    complete = check_mission_complete(op, screen)
    if complete is not None:
        return complete


def check_battle_screen(op: ZOperation, screen: MatLike) -> Optional[str]:
    result = op.round_by_find_area(screen, '战斗画面', '按键-普通攻击')

    if result.is_success:
        return HollowZeroSpecialEvent.IN_BATTLE.value.event_name


def check_mission_complete(op: ZOperation, screen: MatLike) -> Optional[str]:
    result = op.round_by_find_area(screen, '零号空洞-事件', '通关-完成')

    if result.is_success:
        return HollowZeroSpecialEvent.MISSION_COMPLETE.value.event_name
