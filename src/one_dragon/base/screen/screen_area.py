from typing import Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect


class ScreenArea:

    def __init__(self,
                 area_name: str,
                 pc_rect: Rect,
                 text: Optional[str] = None,
                 status: Optional[str] = None,
                 lcs_percent: float = 0.1,
                 template_id: Optional[str] = None,
                 template_sub_dir: Optional[str] = None,
                 template_match_threshold: float = 0.7,
                 pc_alt: bool = False):
        self.area_name: str = area_name
        self.pc_rect: Rect = pc_rect
        self.text: Optional[str] = text
        self.status: Optional[str] = status if status is not None else text
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
        text = ''
        if len(self.template_sub_dir) == 0:
            return self.template_id
        else:
            return f'{self.template_sub_dir}.{self.template_id}'
