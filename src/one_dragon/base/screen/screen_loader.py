import os

from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.base.screen.screen_info import ScreenInfo


class ScreenLoader:

    def __init__(self):
        self._screen_info_list: list[ScreenInfo] = []
        self._screen_info_map: dict[str, ScreenInfo] = {}
        self._screen_area_map: dict[str, ScreenArea] = {}

        self.load_all()

    def load_all(self) -> None:
        """
        加载当前全部的画面
        :return:
        """
        self._screen_info_list.clear()
        self._screen_info_map.clear()
        self._screen_area_map.clear()

        dir_path = ScreenInfo.get_dir_path()
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            if file_name.endswith('.yml') and os.path.isfile(file_path):
                screen_info = ScreenInfo(screen_id=file_name[:-4])
                self._screen_info_list.append(screen_info)
                self._screen_info_map[screen_info.screen_name] = screen_info

                for screen_area in screen_info.area_list:
                    self._screen_area_map[f'{screen_info.screen_name}.{screen_area.area_name}'] = screen_area

    def get_screen(self, screen_name: str) -> ScreenInfo:
        """
        获取某个画面
        :param screen_name:
        :return:
        """
        key = screen_name
        return self._screen_info_map.get(key, None)

    def get_area(self, screen_name: str, area_name: str) -> ScreenArea:
        """
        获取某个区域的信息
        :return:
        """
        key = f'{screen_name}.{area_name}'
        return self._screen_area_map.get(key, None)
