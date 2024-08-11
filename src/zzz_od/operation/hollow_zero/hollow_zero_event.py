import os
import yaml
from enum import Enum
from typing import Optional, List

from one_dragon.utils import os_utils
from one_dragon.utils.log_utils import log


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


class HallowZeroEventService:

    def __init__(self):
        self.normal_events: List[HallowZeroEvent] = []
        self.reload()

    def reload(self):
        self._load_normal_events()

    def _load_normal_events(self):
        dir_path = os_utils.get_path_under_work_dir('assets', 'game_data', 'hollow_zero', 'normal_event')
        file_name_list = os.listdir(dir_path)

        self.normal_events: List[HallowZeroEvent] = []
        for file_name in file_name_list:
            if not file_name.endswith('.yml'):
                continue
            file_path = os.path.join(dir_path, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    event_list: List[dict] = yaml.safe_load(file)
                    events = [HallowZeroEvent(**i) for i in event_list]
                    for e in events:
                        e.on_the_right = True
                    self.normal_events = self.normal_events + events
            except Exception:
                log.error(f'文件读取失败 {file_path}', exc_info=True)

    def get_normal_event_by_name(self, event_name: str) -> Optional[HallowZeroEvent]:
        """
        通过事件名称获取事件
        """
        for event in self.normal_events:
            if event.event_name == event_name:
                return event


class HollowZeroSpecialEvent(Enum):

    RESONIUM_CHOOSE = HallowZeroEvent('选择')
    RESONIUM_CONFIRM_1 = HallowZeroEvent('确认')
    RESONIUM_CONFIRM_2 = HallowZeroEvent('确定')
    RESONIUM_UPGRADE = HallowZeroEvent('催化')

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
