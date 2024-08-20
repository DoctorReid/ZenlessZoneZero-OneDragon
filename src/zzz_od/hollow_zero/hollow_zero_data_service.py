import difflib
import os
import yaml
from typing import List, Optional, Tuple

from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from zzz_od.hollow_zero.game_data.hollow_zero_event import HallowZeroEvent, HollowZeroEntry
from zzz_od.hollow_zero.game_data.hollow_zero_resonium import Resonium


class HallowZeroDataService:

    def __init__(self):
        # 事件
        self.normal_events: List[HallowZeroEvent] = []
        self.entry_list: List[HollowZeroEntry] = []
        self.name_2_entry: dict[str, HollowZeroEntry] = {}

        # 鸣徽
        self.resonium_list: List[Resonium] = []
        self.resonium_cate_list: List[str] = []
        self.cate_2_resonium: dict[str, List[Resonium]] = {}

        self.reload()


    def reload(self):
        self._load_normal_events()
        self._load_entry_list()
        self._load_resonium()

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

    def _load_entry_list(self):
        self.entry_list = []
        self.name_2_entry = {}

        file_path = os_utils.get_path_under_work_dir('assets', 'game_data', 'hollow_zero', 'entry_list.yml')
        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                entry_list: List[dict] = yaml.safe_load(file)
                for i in entry_list:
                    entry = HollowZeroEntry(**i)
                    self.entry_list.append(entry)
                    self.name_2_entry[entry.entry_name] = entry
        except Exception:
            log.error(f'文件读取失败 {file_path}', exc_info=True)

    def get_entry_by_name(self, entry_name: str) -> Optional[HollowZeroEntry]:
        return self.name_2_entry.get(entry_name, None)

    def _load_resonium(self) -> None:
        self.resonium_list = []
        self.resonium_cate_list = []
        self.cate_2_resonium = {}

        file_path = os_utils.get_path_under_work_dir('assets', 'game_data', 'hollow_zero', 'resonium.yml')
        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                entry_list: List[dict] = yaml.safe_load(file)
                for i in entry_list:
                    item = Resonium(**i)
                    self.resonium_list.append(item)
                    if item.category not in self.cate_2_resonium:
                        self.resonium_cate_list.append(item.category)
                        self.cate_2_resonium[item.category] = [item]
                    else:
                        self.cate_2_resonium[item.category].append(item)
        except Exception:
            log.error(f'文件读取失败 {file_path}', exc_info=True)

    def match_resonium_by_ocr(self, cate_ocr: str, name_str: str) -> Optional[Resonium]:
        category_list = [gt(i) for i in self.resonium_cate_list]
        results = difflib.get_close_matches(cate_ocr, category_list, n=1)

        if results is None or len(results) == 0:
            return None

        category_idx = category_list.index(results[0])
        resonium_list = self.cate_2_resonium[self.resonium_cate_list[category_idx]]

        resonium_name_list = [gt(i.name) for i in resonium_list]
        results = difflib.get_close_matches(name_str, resonium_name_list, n=1)

        if results is None or len(results) == 0:
            return None

        resonium_idx = resonium_name_list.index(results[0])
        return resonium_list[resonium_idx]

    def match_resonium_by_ocr_name(self, name_str: str) -> Optional[Resonium]:
        resonium_name_list = [gt(i.name) for i in self.resonium_list]
        results = difflib.get_close_matches(name_str, resonium_name_list, n=1)

        if results is None or len(results) == 0:
            return None

        resonium_idx = resonium_name_list.index(results[0])
        return self.resonium_list[resonium_idx]

    def check_resonium_priority(self, input: str) -> Tuple[List[str], str]:
        """
        校验优先级的文本输入
        错误的输入会被过滤掉
        :param input:
        :return: 匹配的鸣徽和错误信息
        """
        if input is None or len(input) == 0:
            return [], ''

        input_arr = [i.strip() for i in input.split('\n')]
        resonium_list = []
        error_msg = ''
        for i in input_arr:
            if len(i) == 0:
                continue
            split_idx = i.find(' ')
            if split_idx != -1:
                cate_name = i[:split_idx]
                item_name = i[split_idx+1:]
            else:
                cate_name = i
                item_name = ''

            is_valid: bool = False

            for cate in self.resonium_cate_list:
                if item_name != '':  # 不可能是分类
                    break
                if cate_name == cate:
                    resonium_list.append(i)
                    is_valid = True
                    break
            for r in self.resonium_list:
                if cate_name == r.category and item_name == r.name:
                    resonium_list.append(i)
                    is_valid = True
                    break

            if not is_valid:
                error_msg += f'输入非法 {i}'

        return resonium_list, error_msg
