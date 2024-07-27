import time

from enum import Enum
from typing import Callable, List, Optional

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.controller.pc_button import pc_button_utils
from one_dragon.base.controller.pc_button.pc_button_controller import PcButtonController


class XboxButtonEnum(Enum):

    A = ConfigItem('A', 'xbox_0')
    B = ConfigItem('B', 'xbox_1')
    X = ConfigItem('X', 'xbox_2')
    Y = ConfigItem('Y', 'xbox_3')
    LT = ConfigItem('LT', 'xbox_4')
    RT = ConfigItem('RT', 'xbox_5')
    LB = ConfigItem('LB', 'xbox_6')
    RB = ConfigItem('RB', 'xbox_7')


class XboxButtonController(PcButtonController):

    def __init__(self):
        PcButtonController.__init__(self)
        self.pad = None
        if pc_button_utils.is_vgamepad_installed():
            import vgamepad as vg
            self.pad = vg.VX360Gamepad()
            self._btn = vg.XUSB_BUTTON

        self.handler: List[Callable[[Optional[float]], None]] = [
            self.press_a,
            self.press_b,
            self.press_x,
            self.press_y,
            self.press_lt,
            self.press_rt,
            self.press_lb,
            self.press_rb,
        ]

    def tap(self, key: str) -> None:
        """
        触发按键
        :param key:
        :return:
        """
        self.handler[int(key[-1])](None)

    def press_a(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_A, press_time)

    def press_b(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_B, press_time)

    def press_x(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_X, press_time)

    def press_y(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_Y, press_time)

    def press_lt(self, press_time: Optional[float] = None) -> None:
        self.pad.left_trigger(value=255)
        self.pad.update()
        time.sleep(max(self.key_press_time, press_time))
        self.pad.left_trigger(value=0)
        self.pad.update()

    def press_rt(self, press_time: Optional[float] = None) -> None:
        self.pad.right_trigger(value=255)
        self.pad.update()
        time.sleep(max(self.key_press_time, press_time))
        self.pad.right_trigger(value=0)
        self.pad.update()

    def press_lb(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_LEFT_SHOULDER, press_time)

    def press_rb(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_RIGHT_SHOULDER, press_time)

    def _press_button(self, btn, press_time: Optional[float] = None):
        self.pad.press_button(btn)
        self.pad.update()
        time.sleep(max(self.key_press_time, press_time))
        self.pad.release_button(btn)
        self.pad.update()

    def reset(self):
        self.pad.reset()
        self.pad.update()

    def press(self, key: str, press_time: float) -> None:
        """
        :param key: 按键
        :param press_time: 持续按键时间
        :return:
        """
        self.handler[int(key[-1])](press_time)
