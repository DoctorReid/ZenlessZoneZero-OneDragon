import os
from cv2.typing import MatLike
from typing import List, Optional

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.base.yaml_operator import YamlOperator
from one_dragon.utils import os_utils, cv2_utils


class ScreenInfo(YamlOperator):

    def __init__(self, screen_id: Optional[str] = None, create_new: bool = False):
        self.old_screen_id: str = screen_id  # 旧的画面ID 用于保存时删掉旧文件
        self.screen_id: str = screen_id  # 画面ID 用于加载文件
        self.screen_name: str = ''  # 画面名称 用于显示

        self.screen_image: MatLike = None  # 画面图片 存放在 assets/game_data/screen_info
        self.chosen_screen_image: MatLike = None  # 画面图片 从文件系统选择的 是用于新保存的图片

        self.pc_alt: bool = False  # PC端点击是否需要使用ALT键
        self.area_list: List[ScreenArea] = []  # 画面中包含的区域

        if create_new:
            YamlOperator.__init__(self)
        else:
            YamlOperator.__init__(self, self.get_yml_file_path())
            self._init_from_data()

    def get_dir_path(self) -> str:
        """
        文件夹位置
        :return:
        """
        return os_utils.get_path_under_work_dir('assets', 'game_data', 'screen_info', self.screen_id)

    def get_yml_file_path(self) -> str:
        """
        配置文件位置
        :return:
        """
        return os.path.join(self.get_dir_path(), f'{self.screen_id}.yml')

    def get_image_file_path(self) -> str:
        """
        图片位置
        :return:
        """
        return os.path.join(self.get_dir_path(), f'{self.screen_id}.png')

    def _init_from_data(self) -> None:
        """
        从文本中初始化
        :return:
        """
        self.screen_name = self.get('screen_name', '')
        screen_image_path = self.get_image_file_path()
        if os.path.exists(screen_image_path):
            self.screen_image = cv2_utils.read_image(screen_image_path)
        self.pc_alt = self.get('pc_alt', False)

        data_area_list = self.get('area_list', [])
        for data_area in data_area_list:
            pc_rect = data_area.get('pc_rect')
            area = ScreenArea(
                area_name=data_area.get('area_name'),
                pc_rect=Rect(pc_rect[0], pc_rect[1], pc_rect[2], pc_rect[3]),
                text=data_area.get('text'),
                lcs_percent=data_area.get('lcs_percent'),
                template_id=data_area.get('template_id'),
                template_sub_dir=data_area.get('template_sub_dir'),
                template_match_threshold=data_area.get('template_match_threshold'),
                pc_alt=self.pc_alt
            )
            self.area_list.append(area)

    def get_image_to_show(self) -> MatLike:
        """
        用于显示的图片
        :return:
        """
        if self.chosen_screen_image is not None:
            return self.chosen_screen_image
        elif self.screen_image is not None:
            return self.screen_image
        else:
            return None

    def remove_area_by_idx(self, idx: int) -> None:
        """
        删除某行数据
        :param idx:
        :return:
        """
        if self.area_list is None:
            return
        length = len(self.area_list)
        if idx < 0 or idx >= length:
            return
        self.area_list.pop(idx)
