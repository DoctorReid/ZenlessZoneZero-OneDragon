import ctypes
from ctypes.wintypes import RECT

import pyautogui
from pygetwindow import Win32Window

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils.log_utils import log


class PcGameWindow:

    def __init__(self, win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        self.win_title: str = win_title
        self.standard_width: int = standard_width
        self.standard_height: int = standard_height
        self.standard_game_rect: Rect = Rect(0, 0, standard_width, standard_height)

        self.win: Win32Window = None
        self.hWnd = None

        self.init_win()

    def init_win(self) -> None:
        """
        初始化窗口
        :return:
        """
        self.win = None
        self.hWnd = None
        windows = pyautogui.getWindowsWithTitle(self.win_title)
        if len(windows) > 0:
            for win in windows:
                if win.title == self.win_title:
                    self.win = win
                    self.hWnd = win._hWnd
    @property
    def is_win_valid(self) -> bool:
        """
        当前窗口是否正常
        :return:
        """
        return self.win is not None and self.hWnd is not None and ctypes.windll.user32.IsWindow(self.hWnd) != 0

    @property
    def is_win_active(self) -> bool:
        """
        是否当前激活的窗口
        :return:
        """
        return self.win.isActive

    @property
    def is_win_scale(self) -> bool:
        """
        当前窗口是否缩放
        :return:
        """
        if self.win is None:
            return False
        win_rect = self.win_rect

        return not (win_rect.width == self.standard_width and win_rect.height == self.standard_height)

    def active(self) -> bool:
        """
        显示并激活当前窗口
        :return:
        """
        if self.win is None:
            return False
        if self.is_win_active:
            return True
        try:
            try:
                self.win.restore()
                self.win.activate()
                return True
            except Exception:
                # 比较神奇的一个bug 直接activate有可能失败
                # https://github.com/asweigart/PyGetWindow/issues/16#issuecomment-1110207862
                self.win.minimize()
                self.win.restore()
                self.win.activate()
                return True
        except Exception:
            log.error('切换到游戏窗口失败', exc_info=True)
            return False

    @property
    def win_rect(self) -> Rect:
        """
        获取游戏窗口在桌面上面的位置
        Win32Window 里是整个window的信息 参考源码获取里面client部分的
        :return: 游戏窗口信息
        """
        if self.hWnd is None:
            return None
        client_rect = RECT()
        ctypes.windll.user32.GetClientRect(self.hWnd, ctypes.byref(client_rect))
        left_top_pos = ctypes.wintypes.POINT(client_rect.left, client_rect.top)
        ctypes.windll.user32.ClientToScreen(self.hWnd, ctypes.byref(left_top_pos))
        return Rect(left_top_pos.x, left_top_pos.y, left_top_pos.x + client_rect.right, left_top_pos.y + client_rect.bottom)

    def get_scaled_game_pos(self, game_pos: Point) -> Point:
        """
        获取当前分辨率下游戏窗口里的坐标
        :param game_pos: 默认分辨率下的游戏窗口里的坐标
        :return: 当前分辨率下的游戏窗口里坐标
        """
        if self.win is None:
            return None
        rect = self.win_rect
        xs = 1 if rect.width == self.standard_width else rect.width * 1.0 / self.standard_width
        ys = 1 if rect.height == self.standard_height else rect.height * 1.0 / self.standard_height
        s_pos = Point(game_pos.x * xs, game_pos.y * ys)
        return s_pos if self.is_valid_game_pos(s_pos, self.standard_game_rect) else None

    def is_valid_game_pos(self, s_pos: Point, rect: Rect = None) -> bool:
        """
        判断游戏中坐标是否在游戏窗口内
        :param s_pos: 游戏中坐标 已经缩放
        :param rect: 窗口位置信息
        :return: 是否在游戏窗口内
        """
        if self.win is None:
            return False
        if rect is None:
            rect = self.standard_game_rect
        return 0 <= s_pos.x < rect.width and 0 <= s_pos.y < rect.height

    def game2win_pos(self, game_pos: Point) -> Point:
        """
        获取在屏幕中的坐标
        :param game_pos: 默认分辨率下的游戏窗口里的坐标
        :return: 当前分辨率下的屏幕中的坐标
        """
        if self.win is None:
            return None
        rect = self.win_rect
        gp: Point = self.get_scaled_game_pos(game_pos)
        # 缺少一个屏幕边界判断 游戏窗口拖动后可能会超出整个屏幕
        return rect.left_top + gp if gp is not None else None

    def get_dpi(self):
        if self.hWnd is None:
            return None
        return ctypes.windll.user32.GetDpiForWindow(self.hWnd)
