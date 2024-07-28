import time

from cv2.typing import MatLike
from typing import Optional

from one_dragon.base.controller.pc_controller_base import PcControllerBase
from one_dragon.utils import cv2_utils
from zzz_od.config.game_config import GameConfig
from zzz_od.const import game_const
from zzz_od.screen_area.screen_normal_world import ScreenNormalWorldEnum


class ZPcController(PcControllerBase):

    def __init__(self, game_config: GameConfig,
                 win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        PcControllerBase.__init__(self,
                                  win_title=win_title,
                                  standard_width=standard_width,
                                  standard_height=standard_height)

        self.game_config: GameConfig = game_config
        self.key_dodge: str = self.game_config.key_dodge
        self.key_switch_next: str = self.game_config.key_switch_next
        self.key_switch_prev: str = self.game_config.key_switch_prev
        self.key_normal_attack: str = self.game_config.key_normal_attack
        self.key_special_attack: str = self.game_config.key_special_attack
        self.key_ultimate: str = self.game_config.key_ultimate
        self.key_chain_left: str = self.game_config.key_chain_left
        self.key_chain_right: str = self.game_config.key_chain_right

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

    def enable_keyboard(self):
        PcControllerBase.enable_keyboard(self)

        self.key_dodge = self.game_config.key_dodge
        self.key_switch_next = self.game_config.key_switch_next
        self.key_switch_prev = self.game_config.key_switch_prev
        self.key_normal_attack = self.game_config.key_normal_attack
        self.key_special_attack = self.game_config.key_special_attack
        self.key_ultimate: str = self.game_config.key_ultimate
        self.key_chain_left: str = self.game_config.key_chain_left
        self.key_chain_right: str = self.game_config.key_chain_right

    def enable_xbox(self):
        PcControllerBase.enable_xbox(self)

        self.key_dodge = self.game_config.xbox_key_dodge
        self.key_switch_next = self.game_config.xbox_key_switch_next
        self.key_switch_prev = self.game_config.xbox_key_switch_prev
        self.key_normal_attack = self.game_config.xbox_key_normal_attack
        self.key_special_attack = self.game_config.xbox_key_special_attack
        self.key_ultimate: str = self.game_config.xbox_key_ultimate
        self.key_chain_left: str = self.game_config.xbox_key_chain_left
        self.key_chain_right: str = self.game_config.xbox_key_chain_right

    def enable_ds4(self):
        PcControllerBase.enable_ds4(self)

        self.key_dodge = self.game_config.ds4_key_dodge
        self.key_switch_next = self.game_config.ds4_key_switch_next
        self.key_switch_prev = self.game_config.ds4_key_switch_prev
        self.key_normal_attack = self.game_config.ds4_key_normal_attack
        self.key_special_attack = self.game_config.ds4_key_special_attack
        self.key_ultimate: str = self.game_config.ds4_key_ultimate
        self.key_chain_left: str = self.game_config.ds4_key_chain_left
        self.key_chain_right: str = self.game_config.ds4_key_chain_right

    def dodge(self) -> None:
        """
        闪避
        :return:
        """
        self.btn_controller.tap(self.key_dodge)

    def switch_next(self) -> None:
        """
        切换下一个人
        :return:
        """
        self.btn_controller.tap(self.key_switch_next)

    def switch_prev(self) -> None:
        """
        切换上一个人
        :return:
        """
        self.btn_controller.tap(self.key_switch_prev)

    def normal_attack(self, press_time: Optional[float] = None) -> None:
        """
        普通攻击
        """
        if press_time is None:
            self.btn_controller.tap(self.key_normal_attack)
        else:
            self.btn_controller.press(self.key_normal_attack, press_time)

    def special_attack(self, press_time: Optional[float] = None) -> None:
        """
        特殊攻击
        """
        if press_time is None:
            self.btn_controller.tap(self.key_special_attack)
        else:
            self.btn_controller.press(self.key_special_attack, press_time)

    def ultimate(self) -> None:
        """
        终结技
        """
        self.btn_controller.tap(self.key_ultimate)

    def chain_left(self) -> None:
        """
        连携技-左
        """
        self.btn_controller.tap(self.key_chain_left)

    def chain_right(self) -> None:
        """
        连携技-右
        """
        self.btn_controller.tap(self.key_chain_right)
