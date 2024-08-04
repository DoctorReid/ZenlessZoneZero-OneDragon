from collections import OrderedDict

from typing import Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect


class ScreenArea:

    def __init__(self,
                 area_name: str = '',
                 pc_rect: Rect = Rect(0, 0, 0, 0),
                 text: Optional[str] = '',
                 lcs_percent: float = 0.5,
                 template_id: Optional[str] = '',
                 template_sub_dir: Optional[str] = '',
                 template_match_threshold: float = 0.7,
                 pc_alt: bool = False):
        self.area_name: str = area_name
        self.pc_rect: Rect = pc_rect
        self.text: Optional[str] = text
        self.lcs_percent: float = lcs_percent
        self.template_id: Optional[str] = template_id
        self.template_sub_dir: Optional[str] = template_sub_dir
        self.template_match_threshold: float = template_match_threshold
        self.pc_alt: bool = pc_alt  # PC端需要使用ALT后才能点击

    @property
    def rect(self) -> Rect:
        return self.pc_rect

    @property
    def center(self) -> Point:
        return self.rect.center

    @property
    def left_top(self) -> Point:
        return self.rect.left_top

    @property
    def x1(self) -> int:
        return self.rect.x1

    @property
    def x2(self) -> int:
        return self.rect.x2

    @property
    def y1(self) -> int:
        return self.rect.y1

    @property
    def y2(self) -> int:
        return self.rect.y2

    @property
    def width(self) -> int:
        return self.rect.width

    @property
    def height(self) -> int:
        return self.rect.height

    @property
    def template_id_display_text(self) -> str:
        if len(self.template_sub_dir) == 0:
            return self.template_id
        else:
            return f'{self.template_sub_dir}.{self.template_id}'

    @property
    def is_text_area(self) -> bool:
        """
        是否文本区域
        :return:
        """
        return self.text is not None and len(self.text) > 0

    @property
    def is_template_area(self) -> bool:
        """
        是否模板区域
        :return:
        """
        return self.template_id is not None and len(self.template_id) > 0

    def to_order_dict(self) -> dict:
        """
        有顺序的dict 用于保存时候展示
        :return:
        """
        order_dict = dict()
        order_dict['area_name'] = self.area_name
        order_dict['pc_rect'] = [self.pc_rect.x1, self.pc_rect.y1, self.pc_rect.x2, self.pc_rect.y2]
        order_dict['text'] = self.text
        order_dict['lcs_percent'] = self.lcs_percent
        order_dict['template_sub_dir'] = self.template_sub_dir
        order_dict['template_id'] = self.template_id
        order_dict['template_match_threshold'] = self.template_match_threshold

        return order_dict
