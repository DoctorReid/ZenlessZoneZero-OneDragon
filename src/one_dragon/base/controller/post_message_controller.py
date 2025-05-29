import time
import ctypes
import cv2
import numpy as np
from ctypes.wintypes import DWORD, WORD, RECT
from cv2.typing import MatLike
from typing import Optional

from one_dragon.base.controller.controller_base import ControllerBase
from one_dragon.base.controller.pc_game_window import PcGameWindow
from one_dragon.base.geometry.point import Point
from one_dragon.utils.log_utils import log


# Windows结构体定义
class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', DWORD),
        ('biWidth', ctypes.c_long),
        ('biHeight', ctypes.c_long),
        ('biPlanes', WORD),
        ('biBitCount', WORD),
        ('biCompression', DWORD),
        ('biSizeImage', DWORD),
        ('biXPelsPerMeter', ctypes.c_long),
        ('biYPelsPerMeter', ctypes.c_long),
        ('biClrUsed', DWORD),
        ('biClrImportant', DWORD)
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmiColors', DWORD * 3)
    ]


class PostMessageController(ControllerBase):
    """
    基于Windows PostMessage API的控制器
    使用PostMessage发送消息到目标窗口，实现非阻塞式的输入控制
    """

    # Windows消息常量
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    WM_CHAR = 0x0102
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONDOWN = 0x0204
    WM_RBUTTONUP = 0x0205
    WM_MOUSEMOVE = 0x0200
    WM_MOUSEWHEEL = 0x020A

    # 虚拟键码映射
    VK_CODE = {
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46,
        'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C,
        'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52,
        's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
        'y': 0x59, 'z': 0x5A,
        '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35,
        '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39, '0': 0x30,
        'return': 0x0D, 'escape': 0x1B, 'backspace': 0x08, 'tab': 0x09,
        'space': 0x20, 'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,
        'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12, 'win': 0x5B,
    }

    def __init__(self, 
                 win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080,
                 screenshot_alive_seconds: float = 5,
                 max_screenshot_cnt: int = 0):
        """
        初始化PostMessage控制器
        :param win_title: 目标窗口标题
        :param standard_width: 标准宽度
        :param standard_height: 标准高度
        :param screenshot_alive_seconds: 截图存活时间
        :param max_screenshot_cnt: 最大截图数量
        """
        ControllerBase.__init__(self, screenshot_alive_seconds, max_screenshot_cnt)

        self.win_title = win_title
        self.standard_width = standard_width
        self.standard_height = standard_height
        self.game_win: PcGameWindow = PcGameWindow(win_title, standard_width, standard_height)

        # 初始化Windows API
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32

        # 基础API
        self.PostMessage = self.user32.PostMessageW
        self.FindWindow = self.user32.FindWindowW
        self.IsWindowVisible = self.user32.IsWindowVisible
        self.GetWindowRect = self.user32.GetWindowRect

        # 截图相关API
        self.GetWindowDC = self.user32.GetWindowDC
        self.GetClientRect = self.user32.GetClientRect
        self.ReleaseDC = self.user32.ReleaseDC
        self.CreateCompatibleDC = self.gdi32.CreateCompatibleDC
        self.CreateCompatibleBitmap = self.gdi32.CreateCompatibleBitmap
        self.SelectObject = self.gdi32.SelectObject
        self.BitBlt = self.gdi32.BitBlt
        self.DeleteObject = self.gdi32.DeleteObject
        self.DeleteDC = self.gdi32.DeleteDC
        self.GetDIBits = self.gdi32.GetDIBits
        self.PrintWindow = self.user32.PrintWindow

    def init_before_context_run(self) -> bool:
        """运行前初始化"""
        self.game_win.init_win()
        return self.game_win.is_win_valid

    @property
    def is_game_window_ready(self) -> bool:
        """游戏窗口是否已经准备好"""
        return self.game_win.is_win_valid

    def _get_hwnd(self) -> Optional[int]:
        """获取窗口句柄"""
        return self.game_win.get_hwnd()

    def _send_key_message(self, key: str, press_time: float = 0) -> bool:
        """
        发送键盘消息
        :param key: 键名
        :param press_time: 按下时间，0为点击，大于0为长按
        :return: 是否成功
        """
        hwnd = self._get_hwnd()
        if not hwnd:
            log.error(f'未找到窗口: {self.win_title}')
            return False

        if key not in self.VK_CODE:
            log.error(f'不支持的按键: {key}')
            return False

        vk_code = self.VK_CODE[key]

        # 发送按下消息
        result1 = self.PostMessage(hwnd, self.WM_KEYDOWN, vk_code, 0)

        if press_time > 0:
            time.sleep(press_time)

        # 发送释放消息
        result2 = self.PostMessage(hwnd, self.WM_KEYUP, vk_code, 0)

        if not result1 or not result2:
            log.error(f'发送按键消息失败: {key}')
            return False

        return True

    def _send_mouse_message(self, x: int, y: int, message_type: int, wparam: int = 0) -> bool:
        """
        发送鼠标消息
        :param x: x坐标
        :param y: y坐标
        :param message_type: 消息类型
        :param wparam: 附加参数
        :return: 是否成功
        """
        hwnd = self._get_hwnd()
        if not hwnd:
            log.error(f'未找到窗口: {self.win_title}')
            return False

        # 组合坐标参数
        lparam = (y << 16) | (x & 0xFFFF)

        result = self.PostMessage(hwnd, message_type, wparam, lparam)
        if not result:
            log.error(f'发送鼠标消息失败: type={message_type}, pos=({x},{y})')
            return False

        return True

    def click(self, pos: Point = None, press_time: float = 0, pc_alt: bool = False) -> bool:
        """
        点击位置
        :param pos: 点击位置，游戏坐标系
        :param press_time: 按下时间
        :param pc_alt: 是否使用Alt键
        :return: 是否成功
        """
        if pos is None:
            # 如果没有指定位置，点击窗口中心
            pos = Point(self.standard_width // 2, self.standard_height // 2)

        # 转换为窗口坐标
        win_pos = self.game_win.game2win_pos(pos)
        if win_pos is None:
            log.error(f'点击位置超出窗口范围: {pos}')
            return False

        # 转换为窗口内相对坐标
        win_rect = self.game_win.win_rect
        if win_rect is None:
            log.error('无法获取窗口矩形')
            return False

        rel_x = win_pos.x - win_rect.x1
        rel_y = win_pos.y - win_rect.y1

        # Alt键处理
        if pc_alt:
            self._send_key_message('alt', 0.02)
            time.sleep(0.1)

        # 发送鼠标移动
        self._send_mouse_message(rel_x, rel_y, self.WM_MOUSEMOVE)
        time.sleep(0.01)

        # 发送鼠标按下
        self._send_mouse_message(rel_x, rel_y, self.WM_LBUTTONDOWN)

        if press_time > 0:
            time.sleep(press_time)

        # 发送鼠标释放
        self._send_mouse_message(rel_x, rel_y, self.WM_LBUTTONUP)

        if pc_alt:
            time.sleep(0.1)
            self._send_key_message('alt', 0.02)

        return True

    def scroll(self, down: int, pos: Point = None):
        """
        滚动鼠标滚轮
        :param down: 滚动量，正数向下，负数向上
        :param pos: 滚动位置
        """
        if pos is None:
            pos = Point(self.standard_width // 2, self.standard_height // 2)

        win_pos = self.game_win.game2win_pos(pos)
        if win_pos is None:
            log.error(f'滚动位置超出窗口范围: {pos}')
            return

        win_rect = self.game_win.win_rect
        if win_rect is None:
            log.error('无法获取窗口矩形')
            return

        rel_x = win_pos.x - win_rect.x1
        rel_y = win_pos.y - win_rect.y1

        # Windows滚轮消息的delta值，负数向下，正数向上
        delta = -down * 120  # 标准滚轮增量
        wparam = (delta << 16) & 0xFFFF0000

        self._send_mouse_message(rel_x, rel_y, self.WM_MOUSEWHEEL, wparam)

    def drag_to(self, end: Point, start: Point = None, duration: float = 0.5):
        """
        拖拽操作
        :param end: 结束位置
        :param start: 开始位置
        :param duration: 拖拽持续时间
        """
        if start is None:
            start = Point(self.standard_width // 2, self.standard_height // 2)

        start_win = self.game_win.game2win_pos(start)
        end_win = self.game_win.game2win_pos(end)

        if start_win is None or end_win is None:
            log.error('拖拽位置超出窗口范围')
            return

        win_rect = self.game_win.win_rect
        if win_rect is None:
            log.error('无法获取窗口矩形')
            return

        start_rel_x = start_win.x - win_rect.x1
        start_rel_y = start_win.y - win_rect.y1
        end_rel_x = end_win.x - win_rect.x1
        end_rel_y = end_win.y - win_rect.y1

        # 移动到起始位置并按下鼠标
        self._send_mouse_message(start_rel_x, start_rel_y, self.WM_MOUSEMOVE)
        time.sleep(0.01)
        self._send_mouse_message(start_rel_x, start_rel_y, self.WM_LBUTTONDOWN)

        # 计算拖拽路径
        steps = max(10, int(duration * 60))  # 60fps
        for i in range(1, steps + 1):
            progress = i / steps
            current_x = int(start_rel_x + (end_rel_x - start_rel_x) * progress)
            current_y = int(start_rel_y + (end_rel_y - start_rel_y) * progress)

            self._send_mouse_message(current_x, current_y, self.WM_MOUSEMOVE)
            time.sleep(duration / steps)

        # 释放鼠标
        self._send_mouse_message(end_rel_x, end_rel_y, self.WM_LBUTTONUP)

    def input_str(self, to_input: str, interval: float = 0.1):
        """
        输入字符串
        :param to_input: 要输入的文本
        :param interval: 字符间隔时间
        """
        hwnd = self._get_hwnd()
        if not hwnd:
            log.error(f'未找到窗口: {self.win_title}')
            return

        for char in to_input:
            if char in self.VK_CODE:
                self._send_key_message(char)
            else:
                # 对于不在映射表中的字符，使用WM_CHAR消息
                self.PostMessage(hwnd, self.WM_CHAR, ord(char), 0)

            if interval > 0:
                time.sleep(interval)

    def delete_all_input(self):
        """删除所有输入的文本"""
        # Ctrl+A 全选
        self._send_key_message('ctrl', 0.02)
        time.sleep(0.01)
        self._send_key_message('a', 0.02)
        time.sleep(0.1)

        # Delete 删除
        self._send_key_message('backspace', 0.02)

    def press_key(self, key: str, press_time: float = 0.1) -> bool:
        """
        按下指定按键
        :param key: 按键名称
        :param press_time: 按下时间
        :return: 是否成功
        """
        return self._send_key_message(key, press_time)

    def tap_key(self, key: str) -> bool:
        """
        轻击按键
        :param key: 按键名称
        :return: 是否成功
        """
        return self._send_key_message(key, 0.05)

    def get_screenshot(self, independent: bool = False) -> MatLike:
        """
        后台截图实现 - 使用Windows API获取窗口截图
        """

        hwnd = self._get_hwnd()
        if not hwnd:
            log.warning('未找到目标窗口，无法截图')
            return None

        # 获取窗口客户区域大小
        rect = RECT()
        self.GetClientRect(hwnd, ctypes.byref(rect))
        width = rect.right - rect.left
        height = rect.bottom - rect.top

        if width <= 0 or height <= 0:
            log.warning(f'窗口大小无效: {width}x{height}')
            return None

        # 获取窗口设备上下文
        hwndDC = self.GetWindowDC(hwnd)
        if not hwndDC:
            log.warning('无法获取窗口设备上下文')
            return None

            # 创建兼容的设备上下文和位图
        mfcDC = self.CreateCompatibleDC(hwndDC)
        if not mfcDC:
            log.warning('无法创建兼容设备上下文')
            self.ReleaseDC(hwnd, hwndDC)
            return None

        saveBitMap = self.CreateCompatibleBitmap(hwndDC, width, height)
        if not saveBitMap:
            log.warning('无法创建兼容位图')
            self.DeleteDC(mfcDC)
            self.ReleaseDC(hwnd, hwndDC)
            return None

        try:
            # 选择位图到设备上下文
            self.SelectObject(mfcDC, saveBitMap)

            # 复制窗口内容到位图 - 使用PrintWindow获取后台窗口内容
            result = self.PrintWindow(hwnd, mfcDC, 0x00000002)  # PW_CLIENTONLY
            if not result:
                # 如果PrintWindow失败，尝试使用BitBlt
                self.BitBlt(mfcDC, 0, 0, width, height, hwndDC, 0, 0, 0x00CC0020)  # SRCCOPY

            # 获取位图数据
            bmpinfo = BITMAPINFO()
            bmpinfo.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmpinfo.bmiHeader.biWidth = width
            bmpinfo.bmiHeader.biHeight = -height  # 负数表示从上到下
            bmpinfo.bmiHeader.biPlanes = 1
            bmpinfo.bmiHeader.biBitCount = 32
            bmpinfo.bmiHeader.biCompression = 0  # BI_RGB

            # 创建缓冲区
            buffer_size = width * height * 4
            buffer = ctypes.create_string_buffer(buffer_size)

            # 获取DIB数据
            lines = self.GetDIBits(hwndDC, saveBitMap, 0, height, buffer, 
                                 ctypes.byref(bmpinfo), 0)  # DIB_RGB_COLORS

            if lines == 0:
                log.warning('无法获取位图数据')
                return None

            # 转换为numpy数组
            img_array = np.frombuffer(buffer, dtype=np.uint8)
            img_array = img_array.reshape((height, width, 4))

            # 转换BGRA为RGB
            screenshot = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGB)

            # 缩放到标准分辨率
            if self.game_win.is_win_scale:
                screenshot = cv2.resize(screenshot, (self.standard_width, self.standard_height))

            return screenshot

        finally:
            # 清理资源，先创建的后释放
            self.DeleteObject(saveBitMap)
            self.DeleteDC(mfcDC)
            self.ReleaseDC(hwnd, hwndDC)

    def close_game(self):
        """关闭游戏窗口"""
        hwnd = self._get_hwnd()
        if hwnd:
            WM_CLOSE = 0x0010
            self.PostMessage(hwnd, WM_CLOSE, 0, 0)

    def active_window(self) -> None:
        """
        前置窗口
        """
        self.game_win.init_win()
        self.game_win.active()

    def enable_xbox(self):
        """
        启用Xbox控制器
        PostMessage模式下暂不支持手柄输入，保持兼容性
        """
        log.warning('PostMessage模式下不支持Xbox控制器')

    def enable_ds4(self):
        """
        启用DS4控制器
        PostMessage模式下暂不支持手柄输入，保持兼容性
        """
        log.warning('PostMessage模式下不支持DS4控制器')

    def enable_keyboard(self):
        """
        启用键盘控制
        PostMessage模式默认使用键盘控制，无需额外操作
        """
        pass

    def mouse_move(self, game_pos: Point):
        """
        鼠标移动到指定的位置
        :param game_pos: 游戏坐标系中的位置
        """
        win_pos = self.game_win.game2win_pos(game_pos)
        if win_pos is None:
            log.error(f'鼠标移动位置超出窗口范围: {game_pos}')
            return

        win_rect = self.game_win.win_rect
        if win_rect is None:
            log.error('无法获取窗口矩形')
            return

        rel_x = win_pos.x - win_rect.x1
        rel_y = win_pos.y - win_rect.y1

        self._send_mouse_message(rel_x, rel_y, self.WM_MOUSEMOVE)

    def fill_uid_black(self):
        """
        填充UID为黑色 - 可选重写方法
        PostMessage模式下暂不实现此功能
        """
        pass

    def before_screenshot(self):
        """
        截图前的处理 - 可选重写方法
        PostMessage模式下暂不需要特殊处理
        """
        pass
