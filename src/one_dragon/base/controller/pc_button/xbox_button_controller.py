from typing import Callable, List

from enum import Enum

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.controller.pc_button import pc_button_utils


class XboxButtonEnum(Enum):

    A = ConfigItem('A', 'xbox_0')
    B = ConfigItem('B', 'xbox_1')
    X = ConfigItem('X', 'xbox_2')
    Y = ConfigItem('Y', 'xbox_3')
    LT = ConfigItem('LT', 'xbox_4')
    RT = ConfigItem('RT', 'xbox_5')
    LB = ConfigItem('LB', 'xbox_6')
    RB = ConfigItem('RB', 'xbox_7')


class XboxButtonController:

    def __init__(self):
        self.pad = None
        if pc_button_utils.is_vgamepad_installed():
            import vgamepad as vg
            self.pad = vg.VX360Gamepad()
            self._btn = vg.XUSB_BUTTON

        self.handler: List[Callable[[], None]] = [
            self.tap_a,
            self.tap_b,
            self.tap_x,
            self.tap_y,
            self.tap_lt,
            self.tap_rt,
            self.tap_lb,
            self.tap_rb,
        ]

    def tap(self, key: str) -> None:
        """
        触发按键
        :param key:
        :return:
        """
        self.handler[int(key[-1])]()

    def tap_a(self) -> None:
        self.pad.press_button(self._btn.XUSB_GAMEPAD_A)

    def tap_b(self) -> None:
        self.pad.press_button(self._btn.XUSB_GAMEPAD_B)

    def tap_x(self) -> None:
        self.pad.press_button(self._btn.XUSB_GAMEPAD_X)

    def tap_y(self) -> None:
        self.pad.press_button(self._btn.XUSB_GAMEPAD_Y)

    def tap_lt(self) -> None:
        self.pad.left_trigger(value=255)
        self.pad.update()
        self.pad.left_trigger(value=0)
        self.pad.update()

    def tap_rt(self) -> None:
        self.pad.right_trigger(value=255)
        self.pad.update()
        self.pad.right_trigger(value=0)
        self.pad.update()

    def tap_lb(self) -> None:
        self._tap_button(self._btn.XUSB_GAMEPAD_LEFT_SHOULDER)

    def tap_rb(self) -> None:
        self._tap_button(self._btn.XUSB_GAMEPAD_RIGHT_SHOULDER)

    def _tap_button(self, btn):
        self.pad.press_button(btn)
        self.pad.update()
        self.pad.release_button(btn)
        self.pad.update()
