from cv2.typing import MatLike

from one_dragon.base.geometry.point import Point


class ControllerBase:

    def __init__(self):
        """
        基础控制器的定义
        """
        pass

    def init(self) -> bool:
        """
        初始化
        :return:
        """
        return False

    @property
    def is_game_window_ready(self) -> bool:
        """
        游戏窗口是否已经准备好了
        :return:
        """
        return False

    def click(self, pos: Point = None, press_time: float = 0, pc_alt: bool = False) -> bool:
        """
        点击位置
        :param pos: 点击位置 (x,y) 默认分辨率下的游戏窗口里的坐标
        :param press_time: 大于0时长按若干秒
        :param pc_alt: 只在PC端有用 使用ALT键进行点击
        :return: 不在窗口区域时不点击 返回False
        """
        pass

    def screenshot(self) -> MatLike:
        """
        截图 如果分辨率和默认不一样则进行缩放
        :return: 缩放到默认分辨率的截图
        """
        pass

    def scroll(self, down: int, pos: Point = None):
        """
        向下滚动
        :param down: 负数时为相上滚动
        :param pos: 滚动位置 默认分辨率下的游戏窗口里的坐标
        :return:
        """
        pass

    def drag_to(self, end: Point, start: Point = None, duration: float = 0.5):
        """
        按住拖拽
        :param end: 拖拽目的点
        :param start: 拖拽开始点
        :param duration: 拖拽持续时间
        :return:
        """
        pass

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
        pass

    def delete_all_input(self):
        """
        删除所有输入文本
        :return:
        """
        pass
