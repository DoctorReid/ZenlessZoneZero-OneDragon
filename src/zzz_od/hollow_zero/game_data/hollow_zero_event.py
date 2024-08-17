from enum import Enum
from typing import Optional, List


class HollowZeroEntry:

    def __init__(self, entry_name: str, is_benefit: bool = True, need_step: int = 1,
                 is_base: bool = False, can_go: bool = True, is_tp: bool = False):
        # TODO 要将这里改成不可改
        self.entry_name: str = entry_name
        self.is_benefit: bool = is_benefit
        self.need_step: int = need_step
        self.is_base: bool = is_base  # 是否电视机底座
        self.can_go: bool = can_go  # 是否可同行
        self.is_tp: bool = is_tp  # 是否传送点


class HallowZeroNormalEventOption:

    def __init__(self,
                 option_name: str,
                 desc: Optional[str] = None,
                 wait: float = 1,
                 ocr_word: Optional[str] = None,
                 lcs_percent: float = 0.5
                 ):

        self.option_name: str = option_name
        self.desc: str = desc
        self.wait: float = wait  # 选择后等待
        self.ocr_word: str = ocr_word if ocr_word is not None else option_name
        self.lcs_percent: float = lcs_percent


class HallowZeroEvent:

    def __init__(self,
                 event_name: str,
                 entry_name: Optional[str] = None,
                 options: Optional[List[dict]] = None,
                 lcs_percent: float = 1,
                 on_the_right: bool = False
                 ):
        self.entry_name: str = entry_name
        self.event_name: str = event_name
        self.lcs_percent: float = lcs_percent
        if options is not None:
            self.options: List[HallowZeroNormalEventOption] = [HallowZeroNormalEventOption(**i) for i in options]
        else:
            self.options: List[HallowZeroNormalEventOption] = []

        self.on_the_right: bool = on_the_right  # 在右边显示


class HollowZeroSpecialEvent(Enum):

    RESONIUM_CHOOSE = HallowZeroEvent('选择')
    RESONIUM_CONFIRM_1 = HallowZeroEvent('确认')
    RESONIUM_CONFIRM_2 = HallowZeroEvent('确定')
    RESONIUM_UPGRADE = HallowZeroEvent('催化')
    RESONIUM_DROP = HallowZeroEvent('丢弃')

    SWIFT_SUPPLY_LIFE = HallowZeroEvent('回复生命值')
    SWIFT_SUPPLY_COIN = HallowZeroEvent('获取齿轮硬币')
    SWIFT_SUPPLY_PRESS = HallowZeroEvent('降低压力值')

    CORRUPTION_REMOVE = HallowZeroEvent('清除')

    CALL_FOR_SUPPORT = HallowZeroEvent('呼叫增援！', on_the_right=True)
    RESONIUM_STORE_1 = HallowZeroEvent('鸣徽交易', on_the_right=True)
    RESONIUM_STORE_2 = HallowZeroEvent('特价折扣', on_the_right=True)

    CRITICAL_STAGE = HallowZeroEvent('关键进展', on_the_right=True)

    IN_BATTLE = HallowZeroEvent('战斗画面')
    MISSION_COMPLETE = HallowZeroEvent('副本通关')
