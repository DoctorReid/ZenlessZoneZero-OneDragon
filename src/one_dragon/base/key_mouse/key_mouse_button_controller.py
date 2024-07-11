from pynput import keyboard, mouse

from one_dragon.base.key_mouse.key_mouse_def import is_mouse_key, get_mouse_button, get_keyboard_button


class KeyMouseButtonController:

    def __init__(self):
        """
        整合键盘和鼠标的按键控制
        """
        self.keyboard = keyboard.Controller()
        self.mouse = mouse.Controller()

    def tap(self, key: str) -> None:
        """
        按一次按键
        :param key: 按键
        :return:
        """
        if is_mouse_key(key):
            self.mouse.click(get_mouse_button(key))
        else:
            self.keyboard.tap(get_keyboard_button(key))


if __name__ == '__main__':
    _c = KeyMouseButtonController()
    _c.tap('c')
