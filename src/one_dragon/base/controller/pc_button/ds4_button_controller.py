import time

from enum import Enum
from typing import Callable, List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.controller.pc_button import pc_button_utils
from one_dragon.base.controller.pc_button.pc_button_controller import PcButtonController


class Ds4ButtonEnum(Enum):

    CROSS = ConfigItem('X', 'ds4_0')
    CIRCLE = ConfigItem('○', 'ds4_1')
    SQUARE = ConfigItem('□', 'ds4_2')
    TRIANGLE = ConfigItem('△', 'ds4_3')
    L2 = ConfigItem('L2', 'ds4_4')
    R2 = ConfigItem('R2', 'ds4_5')
    L1 = ConfigItem('L1', 'ds4_6')
    R1 = ConfigItem('R1', 'ds4_7')


class Ds4ButtonController(PcButtonController):

    def __init__(self):
        PcButtonController.__init__(self)
        self.pad = None
        if pc_button_utils.is_vgamepad_installed():
            import vgamepad as vg
            self.pad = vg.VDS4Gamepad()
            self._btn = vg.DS4_BUTTONS

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
        self._tap_button(self._btn.DS4_BUTTON_CROSS)

    def tap_b(self) -> None:
        self._tap_button(self._btn.DS4_BUTTON_CIRCLE)

    def tap_x(self) -> None:
        self._tap_button(self._btn.DS4_BUTTON_SQUARE)

    def tap_y(self) -> None:
        self._tap_button(self._btn.DS4_BUTTON_TRIANGLE)

    def tap_lt(self) -> None:
        self.pad.left_trigger(value=255)
        self.pad.update()
        time.sleep(self.key_press_time)
        self.pad.left_trigger(value=0)
        self.pad.update()

    def tap_rt(self) -> None:
        self.pad.right_trigger(value=255)
        self.pad.update()
        time.sleep(self.key_press_time)
        self.pad.right_trigger(value=0)
        self.pad.update()

    def tap_lb(self) -> None:
        self._tap_button(self._btn.DS4_BUTTON_SHOULDER_LEFT)

    def tap_rb(self) -> None:
        self._tap_button(self._btn.DS4_BUTTON_SHOULDER_RIGHT)

    def _tap_button(self, btn):
        self.pad.press_button(btn)
        self.pad.update()
        time.sleep(self.key_press_time)
        self.pad.release_button(btn)
        self.pad.update()

    def reset(self):
        self.pad.reset()
        self.pad.update()
