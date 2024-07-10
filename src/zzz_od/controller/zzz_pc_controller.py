import keyboard
import pyautogui
from cv2.typing import MatLike

from one_dragon.base.controller.pc_controller_base import PcControllerBase
from one_dragon.utils import cv2_utils
from zzz_od.const import game_const
from zzz_od.screen_area.screen_normal_world import ScreenNormalWorldEnum


class ZPcController(PcControllerBase):

    def __init__(self, win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        PcControllerBase.__init__(self,
                                  win_title=win_title,
                                  standard_width=standard_width,
                                  standard_height=standard_height)

    def fill_uid_black(self, screen: MatLike) -> MatLike:
        """
        遮挡UID 由子类实现
        """
        rect = ScreenNormalWorldEnum.UID.value.rect

        return cv2_utils.mark_area_as_color(
            screen,
            pos=[rect.x1, rect.y1, rect.width, rect.height],
            color=game_const.YOLO_DEFAULT_COLOR,
            new_image=True
        )

    def switch_next(self) -> None:
        """
        切换下一个人
        :return:
        """
        keyboard.send('c')
