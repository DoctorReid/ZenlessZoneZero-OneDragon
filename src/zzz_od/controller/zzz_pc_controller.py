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
        self.key_move_w: str = self.game_config.key_move_w
        self.key_move_s: str = self.game_config.key_move_s
        self.key_move_a: str = self.game_config.key_move_a
        self.key_move_d: str = self.game_config.key_move_d
        self.key_interact: str = self.game_config.key_interact

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
        self.key_move_w: str = self.game_config.key_move_w
        self.key_move_s: str = self.game_config.key_move_s
        self.key_move_a: str = self.game_config.key_move_a
        self.key_move_d: str = self.game_config.key_move_d
        self.key_interact: str = self.game_config.key_interact

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
        self.key_move_w: str = self.game_config.xbox_key_move_w
        self.key_move_s: str = self.game_config.xbox_key_move_s
        self.key_move_a: str = self.game_config.xbox_key_move_a
        self.key_move_d: str = self.game_config.xbox_key_move_d
        self.key_interact: str = self.game_config.xbox_key_interact

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
        self.key_move_w: str = self.game_config.ds4_key_move_w
        self.key_move_s: str = self.game_config.ds4_key_move_s
        self.key_move_a: str = self.game_config.ds4_key_move_a
        self.key_move_d: str = self.game_config.ds4_key_move_d
        self.key_interact: str = self.game_config.ds4_key_interact

    def dodge(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        闪避
        :return:
        """
        if press:
            self.btn_controller.press(self.key_dodge, press_time)
        elif release:
            self.btn_controller.release(self.key_dodge)
        else:
            self.btn_controller.tap(self.key_dodge)

    def switch_next(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        切换角色-下一个
        :return:
        """
        if press:
            self.btn_controller.press(self.key_switch_next, press_time)
        elif release:
            self.btn_controller.release(self.key_switch_next)
        else:
            self.btn_controller.tap(self.key_switch_next)

    def switch_prev(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        切换角色-上一个
        :return:
        """
        if press:
            self.btn_controller.press(self.key_switch_prev, press_time)
        elif release:
            self.btn_controller.release(self.key_switch_prev)
        else:
            self.btn_controller.tap(self.key_switch_prev)

    def normal_attack(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        普通攻击
        """
        if press:
            self.btn_controller.press(self.key_normal_attack, press_time)
        elif release:
            self.btn_controller.release(self.key_normal_attack)
        else:
            self.btn_controller.tap(self.key_normal_attack)

    def special_attack(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        特殊攻击
        """
        if press:
            self.btn_controller.press(self.key_special_attack, press_time)
        elif release:
            self.btn_controller.release(self.key_special_attack)
        else:
            self.btn_controller.tap(self.key_special_attack)

    def ultimate(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        终结技
        """
        if press:
            self.btn_controller.press(self.key_ultimate, press_time)
        elif release:
            self.btn_controller.release(self.key_ultimate)
        else:
            self.btn_controller.tap(self.key_ultimate)

    def chain_left(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        连携技-左
        """
        if press:
            self.btn_controller.press(self.key_chain_left, press_time)
        elif release:
            self.btn_controller.release(self.key_chain_left)
        else:
            self.btn_controller.tap(self.key_chain_left)

    def chain_right(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        连携技-右
        """
        if press:
            self.btn_controller.press(self.key_chain_right, press_time)
        elif release:
            self.btn_controller.release(self.key_chain_right)
        else:
            self.btn_controller.tap(self.key_chain_right)

    def move_w(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        向前移动
        :return:
        """
        if press:
            self.btn_controller.press(self.key_move_w, press_time)
        elif release:
            self.btn_controller.release(self.key_move_w)
        else:
            self.btn_controller.tap(self.key_move_w)

    def move_s(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        向后移动
        """
        if press:
            self.btn_controller.press(self.key_move_s, press_time)
        elif release:
            self.btn_controller.release(self.key_move_s)
        else:
            self.btn_controller.tap(self.key_move_s)

    def move_a(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        向左移动
        """
        if press:
            self.btn_controller.press(self.key_move_a, press_time)
        elif release:
            self.btn_controller.release(self.key_move_a)
        else:
            self.btn_controller.tap(self.key_move_a)

    def move_d(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        向右移动
        """
        if press:
            self.btn_controller.press(self.key_move_d, press_time)
        elif release:
            self.btn_controller.release(self.key_move_d)
        else:
            self.btn_controller.tap(self.key_move_d)

    def interact(self, press: bool = False, press_time: Optional[float] = None, release: bool = False) -> None:
        """
        交互
        """
        if press:
            self.btn_controller.press(self.key_interact, press_time)
        elif release:
            self.btn_controller.release(self.key_interact)
        else:
            self.btn_controller.tap(self.key_interact)
