from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from pynput import keyboard, mouse


_key_mouse_btn_listener_executor = ThreadPoolExecutor(thread_name_prefix='od_key_mouse_btn_listener', max_workers=8)


class KeyMouseButtonListener:

    def __init__(self,
                 on_button_tap: Callable[[str], None]
                 ):
        self.keyboard_listener = keyboard.Listener(on_press=self._on_keyboard_press)
        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)

        self.on_button_tap: Callable[[str], None] = on_button_tap

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
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop(self):
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
