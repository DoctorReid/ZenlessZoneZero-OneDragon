import time

import ctypes
import cv2
import numpy as np
import pyautogui
from PIL.Image import Image
from cv2.typing import MatLike
from functools import lru_cache

from one_dragon.base.controller.controller_base import ControllerBase
from one_dragon.base.controller.pc_button.pc_button_controller import PcButtonController
from one_dragon.base.controller.pc_game_window import PcGameWindow
from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils.log_utils import log


class PcControllerBase(ControllerBase):

    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    def __init__(self, win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        ControllerBase.__init__(self)
        self.standard_width: int = standard_width
        self.standard_height: int = standard_height
        self.game_win: PcGameWindow = PcGameWindow(win_title,
                                                   standard_width=standard_width, standard_height=standard_height)
        self.btn_controller: PcButtonController = PcButtonController()

    def init(self) -> bool:
        self.game_win.init_win()
        return self.game_win.active()

    @property
    def is_game_window_ready(self) -> bool:
        """
        游戏窗口是否已经准备好了
        :return:
        """
        return self.game_win.is_win_valid

    def click(self, pos: Point = None, press_time: float = 0, pc_alt: bool = False) -> bool:
        """
        点击位置
        :param pos: 游戏中的位置 (x,y)
        :param press_time: 大于0时长按若干秒
        :param pc_alt: 只在PC端有用 使用ALT键进行点击
        :return: 不在窗口区域时不点击 返回False
        """
        click_pos: Point
        if pos is not None:
            click_pos: Point = self.game_win.game2win_pos(pos)
            if click_pos is None:
                log.error('点击非游戏窗口区域 (%s)', pos)
                return False
        else:
            click_pos = get_current_mouse_pos()

        if pc_alt:
            pyautogui.keyDown('alt')
            time.sleep(0.01)
        win_click(click_pos, press_time=press_time)
        if pc_alt:
            pyautogui.keyUp('alt')
        return True

    def get_screenshot(self) -> MatLike:
        """
        截图 如果分辨率和默认不一样则进行缩放
        :return: 截图
        """
        rect: Rect = self.game_win.win_rect
        img = screenshot(rect.x1, rect.y1, rect.width, rect.height)
        result = cv2.resize(img, (self.standard_width, self.standard_height)) if self.game_win.is_win_scale else img
        return result

    def scroll(self, down: int, pos: Point = None):
        """
        向下滚动
        :param down: 负数时为相上滚动
        :param pos: 滚动位置 默认分辨率下的游戏窗口里的坐标
        :return:
        """
        if pos is None:
            pos = get_current_mouse_pos()
        win_pos = self.game_win.game2win_pos(pos)
        win_scroll(down, win_pos)

    def drag_to(self, end: Point, start: Point = None, duration: float = 0.5):
        """
        按住拖拽
        :param end: 拖拽目的点
        :param start: 拖拽开始点
        :param duration: 拖拽持续时间
        :return:
        """
        from_pos: Point
        if start is None:
            from_pos = get_current_mouse_pos()
        else:
            from_pos = self.game_win.game2win_pos(start)

        to_pos = self.game_win.game2win_pos(end)
        drag_mouse(from_pos, to_pos, duration=duration)

    def close_game(self):
        """
        关闭游戏
        :return:
        """
        pass

    def input_str(self, to_input: str, interval: float = 0.1):
        """
        输入文本 需要自己先选择好输入框
        :param to_input: 文本
        :param interval: 输入间隙 秒
        :return:
        """
        pyautogui.typewrite(to_input, interval)

    def delete_all_input(self):
        """
        删除所有输入文本
        :return:
        """
        pyautogui.press('delete')


def win_click(pos: Point = None, press_time: float = 0, primary: bool = True):
    """
    点击鼠标
    :param pos: 屏幕坐标
    :param press_time: 按住时间
    :param primary: 是否点击鼠标主要按键（通常是左键）
    :return:
    """
    btn = pyautogui.PRIMARY if primary else pyautogui.SECONDARY
    if pos is None:
        pos = get_current_mouse_pos()
    if press_time > 0:
        pyautogui.moveTo(pos.x, pos.y)
        pyautogui.mouseDown(button=btn)
        time.sleep(press_time)
        pyautogui.mouseUp(button=btn)
    else:
        pyautogui.click(pos.x, pos.y, button=btn)


def win_scroll(clicks: int, pos: Point = None):
    """
    向下滚动
    :param clicks: 负数时为相上滚动
    :param pos: 滚动位置 不传入时为鼠标当前位置
    :return:
    """
    if pos is not None:
        pyautogui.moveTo(pos.x, pos.y)
    d = 2000 if get_mouse_sensitivity() <= 10 else 1000
    pyautogui.scroll(-d * clicks, pos.x, pos.y)


@lru_cache
def get_mouse_sensitivity():
    """
    获取鼠标灵敏度
    :return:
    """
    user32 = ctypes.windll.user32
    speed = ctypes.c_int()
    user32.SystemParametersInfoA(0x0070, 0, ctypes.byref(speed), 0)
    return speed.value


def drag_mouse(start: Point, end: Point, duration: float = 0.5):
    """
    按住鼠标左键进行画面拖动
    :param start: 原位置
    :param end: 拖动位置
    :param duration: 拖动鼠标到目标位置，持续秒数
    :return:
    """
    pyautogui.moveTo(start.x, start.y)  # 将鼠标移动到起始位置
    pyautogui.dragTo(end.x, end.y, duration=duration)


def get_current_mouse_pos() -> Point:
    """
    获取鼠标当前坐标
    :return:
    """
    pos = pyautogui.position()
    return Point(pos.x, pos.y)


def screenshot(left, top, width, height) -> MatLike:
    """
    对屏幕区域截图
    :param left:
    :param top:
    :param width:
    :param height:
    :return:
    """
    img: Image = pyautogui.screenshot(region=(left, top, width, height))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)