from functools import lru_cache
from typing import Union

from pynput import mouse, keyboard


@lru_cache
def is_mouse_key(key: str) -> bool:
    """
    是否鼠标按键
    :param key:
    :return:
    """
    return key.startswith('mouse_')


@lru_cache
def get_button(key: str):
    if is_mouse_key(key):
        return get_mouse_button(key)
    else:
        return get_keyboard_button(key)


@lru_cache
def get_mouse_button(key: str) -> mouse.Button:
    real_key = key[6:]  # 取mouse_之后的部分
    return mouse.Button[real_key]


@lru_cache
def get_keyboard_button(key: str) -> Union[keyboard.KeyCode, keyboard.Key, str]:
    if key in keyboard.Key.__members__:
        return keyboard.Key[key]
    elif len(key) == 1:
        return keyboard.KeyCode.from_char(key)
    else:
        return key
