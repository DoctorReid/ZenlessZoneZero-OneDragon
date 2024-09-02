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
    L_STICK_W = ConfigItem('左摇杆-上', 'xbox_8')
    L_STICK_S = ConfigItem('左摇杆-下', 'xbox_9')
    L_STICK_A = ConfigItem('左摇杆-左', 'xbox_10')
    L_STICK_D = ConfigItem('左摇杆-右', 'xbox_11')


class XboxButtonController(PcButtonController):

    def __init__(self):
        PcButtonController.__init__(self)
        self.pad = None
        if pc_button_utils.is_vgamepad_installed():
            import vgamepad as vg
            self.pad = vg.VX360Gamepad()
            self._btn = vg.XUSB_BUTTON

        self._tab_handler: List[Callable[[Optional[float]], None]] = [
            self.tab_a,
            self.tab_b,
            self.tab_x,
            self.tab_y,
            self.tab_lt,
            self.tab_rt,
            self.tab_lb,
            self.tab_rb,
            self.tab_l_stick_w,
            self.tab_l_stick_s,
            self.tab_l_stick_a,
            self.tab_l_stick_d,
        ]

        self.release_handler: List[Callable[[], None]] = [
            self.release_a,
            self.release_b,
            self.release_x,
            self.release_y,
            self.release_lt,
            self.release_rt,
            self.release_lb,
            self.release_rb,
            self.release_l_stick,
            self.release_l_stick,
            self.release_l_stick,
            self.release_l_stick,
        ]

    def tap(self, key: str) -> None:
        """
        触发按键
        :param key:
        :return:
        """
        if key is None:  # 部分按键不支持
            return
        self._tab_handler[int(key.split('_')[-1])](None)

    def tab_a(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_A, press_time)

    def tab_b(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_B, press_time)

    def tab_x(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_X, press_time)

    def tab_y(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_Y, press_time)

    def tab_lt(self, press_time: Optional[float] = None) -> None:
        self.pad.left_trigger(value=255)
        self.pad.update()
        if press_time is None:
            press_time = 0
        time.sleep(max(self.key_press_time, press_time))
        self.pad.left_trigger(value=0)
        self.pad.update()

    def tab_rt(self, press_time: Optional[float] = None) -> None:
        self.pad.right_trigger(value=255)
        self.pad.update()
        if press_time is None:
            press_time = 0
        time.sleep(max(self.key_press_time, press_time))
        self.pad.right_trigger(value=0)
        self.pad.update()

    def tab_lb(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_LEFT_SHOULDER, press_time)

    def tab_rb(self, press_time: Optional[float] = None) -> None:
        self._press_button(self._btn.XUSB_GAMEPAD_RIGHT_SHOULDER, press_time)

    def tab_l_stick_w(self, press_time: Optional[float] = None) -> None:
        self.pad.left_joystick_float(0, -1)
        self.pad.update()
        if press_time is None:
            press_time = 0
        time.sleep(max(self.key_press_time, press_time))
        self.pad.left_joystick_float(0, 0)
        self.pad.update()

    def tab_l_stick_s(self, press_time: Optional[float] = None) -> None:
        self.pad.left_joystick_float(0, 1)
        self.pad.update()
        if press_time is None:
            press_time = 0
        time.sleep(max(self.key_press_time, press_time))
        self.pad.left_joystick_float(0, 0)
        self.pad.update()

    def tab_l_stick_a(self, press_time: Optional[float] = None) -> None:
        self.pad.left_joystick_float(-1, 0)
        self.pad.update()
        if press_time is None:
            press_time = 0
        time.sleep(max(self.key_press_time, press_time))
        self.pad.left_joystick_float(0, 0)
        self.pad.update()

    def tab_l_stick_d(self, press_time: Optional[float] = None) -> None:
        self.pad.left_joystick_float(1, 0)
        self.pad.update()
        if press_time is None:
            press_time = 0
        time.sleep(max(self.key_press_time, press_time))
        self.pad.left_joystick_float(0, 0)
        self.pad.update()

    def _press_button(self, btn, press_time: Optional[float] = None):
        self.pad.press_button(btn)
        self.pad.update()
        if press_time is None:
            press_time = 0
        time.sleep(max(self.key_press_time, press_time))
        self.pad.release_button(btn)
        self.pad.update()

    def reset(self):
        self.pad.reset()
        self.pad.update()

    def press(self, key: str, press_time: Optional[float] = None) -> None:
        """
        :param key: 按键
        :param press_time: 持续按键时间
        :return:
        """
        if key is None:  # 部分按键不支持
            return
        self._tab_handler[int(key.split('_')[-1])](press_time)

    def release(self, key: str) -> None:
        if key is None:  # 部分按键不支持
            return
        self.release_handler[int(key.split('_')[-1])]()

    def release_a(self) -> None:
        self._release_btn(self._btn.XUSB_GAMEPAD_A)

    def release_b(self) -> None:
        self._release_btn(self._btn.XUSB_GAMEPAD_B)

    def release_x(self) -> None:
        self._release_btn(self._btn.XUSB_GAMEPAD_X)

    def release_y(self) -> None:
        self._release_btn(self._btn.XUSB_GAMEPAD_Y)

    def release_lt(self) -> None:
        self.pad.left_trigger(value=0)
        self.pad.update()

    def release_rt(self) -> None:
        self.pad.right_trigger(value=0)
        self.pad.update()

    def release_lb(self) -> None:
        self._release_btn(self._btn.XUSB_GAMEPAD_LEFT_SHOULDER)

    def release_rb(self) -> None:
        self._release_btn(self._btn.XUSB_GAMEPAD_RIGHT_SHOULDER)

    def release_l_stick(self) -> None:
        self.pad.left_joystick_float(0, 0)
        self.pad.update()

    def _release_btn(self, btn) -> None:
        """
        释放具体按键
        """
        self.pad.release_button(btn)
        self.pad.update()
