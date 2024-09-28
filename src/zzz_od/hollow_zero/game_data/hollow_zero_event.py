from enum import Enum
from typing import Optional, List


class HollowZeroEntry:

    def __init__(self, entry_name: str, is_benefit: bool = True, need_step: int = 1,
                 is_base: bool = False, can_go: bool = True, is_tp: bool = False,
                 move_afterwards: bool = False):
        # TODO 要将这里改成不可改
        self.entry_id: str = entry_name[:4]
        self.entry_name: str = entry_name[5:]
        self.is_benefit: bool = is_benefit  # 是否完全有益的事件
        self.need_step: int = need_step
        self.is_base: bool = is_base  # 是否电视机底座
        self.can_go: bool = can_go  # 是否可通行
        self.is_tp: bool = is_tp  # 是否传送点
        self.move_afterwards: bool = move_afterwards  # 进入后会触发额外移动 轨道、弹射等


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
                 on_the_right: bool = False,
                 is_entry_opt: bool = False
                 ):
        self.entry_name: str = entry_name
        self.event_name: str = event_name
        self.lcs_percent: float = lcs_percent
        if options is not None:
            self.options: List[HallowZeroNormalEventOption] = [HallowZeroNormalEventOption(**i) for i in options]
        else:
            self.options: List[HallowZeroNormalEventOption] = []

        self.on_the_right: bool = on_the_right  # 在右边显示
        self.is_entry_opt: bool = is_entry_opt  # 是否用于进入格子的选项 例如 进入商店


class HollowZeroSpecialEvent(Enum):

    HOLLOW_INSIDE = HallowZeroEvent('空洞内部')

    RESONIUM_CHOOSE = HallowZeroEvent('选择')
    RESONIUM_CONFIRM_1 = HallowZeroEvent('确认')
    RESONIUM_CONFIRM_2 = HallowZeroEvent('确定')
    RESONIUM_UPGRADE = HallowZeroEvent('催化')
    RESONIUM_DROP = HallowZeroEvent('丢弃')
    RESONIUM_DROP_2 = HallowZeroEvent('抵押欠款')
    RESONIUM_SWITCH = HallowZeroEvent('交换')

    SWIFT_SUPPLY_LIFE = HallowZeroEvent('回复生命值')
    SWIFT_SUPPLY_COIN = HallowZeroEvent('获取齿轮硬币')
    SWIFT_SUPPLY_PRESS = HallowZeroEvent('降低压力值')

    CORRUPTION_REMOVE = HallowZeroEvent('清除')

    CALL_FOR_SUPPORT = HallowZeroEvent('呼叫增援！', on_the_right=True)
    RESONIUM_STORE_0 = HallowZeroEvent('欢迎光临！本店只收齿轮硬币～', on_the_right=True)
    RESONIUM_STORE_1 = HallowZeroEvent('欢迎本店欢迎', on_the_right=True)
    RESONIUM_STORE_2 = HallowZeroEvent('鸣徽交易', on_the_right=True)
    RESONIUM_STORE_3 = HallowZeroEvent('特价折扣', on_the_right=True)
    RESONIUM_STORE_4 = HallowZeroEvent('鸣徽催化', on_the_right=True)
    RESONIUM_STORE_5 = HallowZeroEvent('进入商店', on_the_right=True, is_entry_opt=True)

    CRITICAL_STAGE_ENTRY = HallowZeroEvent('进入守门人决斗', on_the_right=True, is_entry_opt=True)
    CRITICAL_STAGE_ENTRY_2 = HallowZeroEvent('进入危险目标决斗', on_the_right=True, is_entry_opt=True)

    IN_BATTLE = HallowZeroEvent('战斗画面')
    MISSION_COMPLETE = HallowZeroEvent('副本通关')

    FULL_IN_BAG = HallowZeroEvent('背包已满')
    OLD_CAPITAL = HallowZeroEvent('旧都失物')

    DOOR_BATTLE_ENTRY = HallowZeroEvent('开门', on_the_right=True, is_entry_opt=True)
