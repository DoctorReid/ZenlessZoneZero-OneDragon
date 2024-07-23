from pynput import keyboard, mouse

from one_dragon.base.controller.pc_button import pc_button_utils


class PcButtonController:

    def __init__(self):
        self.keyboard = keyboard.Controller()
        self.mouse = mouse.Controller()
        self.xbox = None
        self.ds4 = None

        self.xbox_btn_map: dict[str, int] = {}

    def enable_xbox(self):
        if pc_button_utils.is_vgamepad_installed():
            import vgamepad as vg
            self.xbox = vg.VX360Gamepad()

    def enable_ds4(self):
        if pc_button_utils.is_vgamepad_installed():
            import vgamepad as vg
            self.ds4 = vg.VDS4Gamepad()

    def tap(self, key: str) -> None:
        """
        按一次按键
        :param key: 按键
        :return:
        """
        if pc_button_utils.is_mouse_button(key):
            self.mouse.click(pc_button_utils.get_mouse_button(key))
        elif self.xbox is not None and pc_button_utils.is_xbox_button(key):
            pass
        elif self.ds4 is not None and pc_button_utils.is_ds4_button(key):
            pass
        else:
            self.keyboard.tap(pc_button_utils.get_keyboard_button(key))
