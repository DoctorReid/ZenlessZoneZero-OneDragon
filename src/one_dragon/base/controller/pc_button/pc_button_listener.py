from concurrent.futures import ThreadPoolExecutor

from pynput import keyboard, mouse
from typing import Callable

_key_mouse_btn_listener_executor = ThreadPoolExecutor(thread_name_prefix='od_key_mouse_btn_listener', max_workers=8)


class PcButtonListener:

    def __init__(self,
                 on_button_tap: Callable[[str], None],
                 listen_keyboard: bool = False,
                 listen_mouse: bool = False,
                 listen_gamepad: bool = False,
                 ):
        self.keyboard_listener = keyboard.Listener(on_press=self._on_keyboard_press)
        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self.gamepad_listener = None

        self.on_button_tap: Callable[[str], None] = on_button_tap

        self.listen_keyboard: bool = listen_keyboard
        self.listen_mouse: bool = listen_mouse
        self.listen_gamepad: bool = listen_gamepad

    def _on_keyboard_press(self, event):
        if isinstance(event, keyboard.Key):
            k = event.name
        elif isinstance(event, keyboard.KeyCode):
            k = event.char
        else:
            return

        self._call_button_tap_callback(k)

    def _on_mouse_click(self, x, y, button: mouse.Button, pressed):
        if pressed == 1:
            self._call_button_tap_callback('mouse_' + button.name)

    def _call_button_tap_callback(self, key: str) -> None:
        if self.on_button_tap is not None:
            _key_mouse_btn_listener_executor.submit(self.on_button_tap, key)

    def start(self):
        if self.listen_keyboard:
            self.keyboard_listener.start()
        if self.listen_mouse:
            self.mouse_listener.start()

    def stop(self):
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
