import time
from typing import Optional

from one_dragon.base.controller.pc_controller_base import PcControllerBase
from one_dragon.base.controller.post_message_controller import PostMessageController
from one_dragon.base.geometry.point import Point
from one_dragon.utils.log_utils import log
from cv2.typing import MatLike


class HybridController(PcControllerBase):
    """
    混合控制器 - 优先使用PostMessage，回退到PC控制器
    继承PcControllerBase，集成PostMessageController的功能
    能用PostMessage的方法就用，不能用的则使用PC控制器的方法
    """

    def __init__(self, win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        """
        初始化混合控制器
        :param win_title: 目标窗口标题
        :param standard_width: 标准宽度
        :param standard_height: 标准高度
        """
        # 初始化基础PC控制器
        PcControllerBase.__init__(self, win_title, standard_width, standard_height)
        
        # 初始化PostMessage控制器
        self.post_message_controller = PostMessageController(
            win_title=win_title,
            standard_width=standard_width,
            standard_height=standard_height
        )
        
        # 标记PostMessage是否可用
        self._post_message_available = True

    def init_before_context_run(self) -> bool:
        """运行前初始化"""
        # 首先尝试初始化PostMessage控制器
        post_msg_success = self.post_message_controller.init_before_context_run()
        if not post_msg_success:
            log.warning('PostMessage控制器初始化失败，将回退到PC控制器')
            self._post_message_available = False
        
        # 初始化基础PC控制器
        pc_success = PcControllerBase.init_before_context_run(self)
        
        return post_msg_success or pc_success

    def click(self, pos: Point = None, press_time: float = 0, pc_alt: bool = False) -> bool:
        """
        点击位置 - 优先使用PostMessage
        :param pos: 点击位置
        :param press_time: 按下时间
        :param pc_alt: 是否使用Alt键
        :return: 是否成功
        """
        if self._post_message_available:
            try:
                result = self.post_message_controller.click(pos, press_time, pc_alt)
                if result:
                    return True
                else:
                    log.warning('PostMessage点击失败，尝试回退到PC控制器')
            except Exception as e:
                log.warning(f'PostMessage点击异常: {e}，尝试回退到PC控制器')
                self._post_message_available = False

        # 回退到PC控制器
        return PcControllerBase.click(self, pos, press_time, pc_alt)

    def scroll(self, down: int, pos: Point = None):
        """
        滚动鼠标滚轮 - 优先使用PostMessage
        :param down: 滚动量
        :param pos: 滚动位置
        """
        if self._post_message_available:
            try:
                self.post_message_controller.scroll(down, pos)
                return
            except Exception as e:
                log.warning(f'PostMessage滚动异常: {e}，尝试回退到PC控制器')
                self._post_message_available = False

        # 回退到PC控制器
        PcControllerBase.scroll(self, down, pos)

    def drag_to(self, end: Point, start: Point = None, duration: float = 0.5):
        """
        拖拽操作 - 优先使用PostMessage
        :param end: 结束位置
        :param start: 开始位置
        :param duration: 拖拽持续时间
        """
        if self._post_message_available:
            try:
                self.post_message_controller.drag_to(end, start, duration)
                return
            except Exception as e:
                log.warning(f'PostMessage拖拽异常: {e}，尝试回退到PC控制器')
                self._post_message_available = False

        # 回退到PC控制器
        PcControllerBase.drag_to(self, end, start, duration)

    def input_str(self, to_input: str, interval: float = 0.1):
        """
        输入字符串 - 优先使用PostMessage
        :param to_input: 要输入的文本
        :param interval: 字符间隔时间
        """
        if self._post_message_available:
            try:
                self.post_message_controller.input_str(to_input, interval)
                return
            except Exception as e:
                log.warning(f'PostMessage输入异常: {e}，尝试回退到PC控制器')
                self._post_message_available = False

        # 回退到PC控制器
        PcControllerBase.input_str(self, to_input, interval)

    def delete_all_input(self):
        """删除所有输入的文本 - 优先使用PostMessage"""
        if self._post_message_available:
            try:
                self.post_message_controller.delete_all_input()
                return
            except Exception as e:
                log.warning(f'PostMessage删除输入异常: {e}，尝试回退到PC控制器')
                self._post_message_available = False

        # PC控制器没有实现此方法，使用键盘快捷键
        try:
            from pynput import keyboard
            kb = keyboard.Controller()
            # Ctrl+A 全选
            with kb.pressed(keyboard.Key.ctrl):
                kb.press('a')
                kb.release('a')
            time.sleep(0.1)
            # Delete 删除
            kb.press(keyboard.Key.backspace)
            kb.release(keyboard.Key.backspace)
        except Exception as e:
            log.error(f'删除输入失败: {e}')

    def press_key(self, key: str, press_time: float = 0.1) -> bool:
        """
        按下指定按键 - 优先使用PostMessage
        :param key: 按键名称
        :param press_time: 按下时间
        :return: 是否成功
        """
        if self._post_message_available:
            try:
                result = self.post_message_controller.press_key(key, press_time)
                if result:
                    return True
                else:
                    log.warning('PostMessage按键失败，尝试回退到PC控制器')
            except Exception as e:
                log.warning(f'PostMessage按键异常: {e}，尝试回退到PC控制器')
                self._post_message_available = False

        # 回退到键盘控制器
        try:
            from pynput import keyboard
            kb = keyboard.Controller()
            if hasattr(keyboard.Key, key):
                # 特殊按键
                special_key = getattr(keyboard.Key, key)
                kb.press(special_key)
                time.sleep(press_time)
                kb.release(special_key)
            else:
                # 普通字符
                kb.press(key)
                time.sleep(press_time)
                kb.release(key)
            return True
        except Exception as e:
            log.error(f'按键失败: {e}')
            return False

    def tap_key(self, key: str) -> bool:
        """
        轻击按键 - 优先使用PostMessage
        :param key: 按键名称
        :return: 是否成功
        """
        if self._post_message_available:
            try:
                result = self.post_message_controller.tap_key(key)
                if result:
                    return True
                else:
                    log.warning('PostMessage轻击失败，尝试回退到PC控制器')
            except Exception as e:
                log.warning(f'PostMessage轻击异常: {e}，尝试回退到PC控制器')
                self._post_message_available = False

        # 回退到键盘控制器
        return self.press_key(key, 0.05)

    def get_screenshot(self, independent: bool = False) -> MatLike:
        """
        截图 - 优先使用PostMessage的后台截图功能
        :param independent: 是否独立截图
        :return: 截图
        """
        if self._post_message_available:
            try:
                screenshot = self.post_message_controller.get_screenshot(independent)
                if screenshot is not None:
                    return screenshot
                else:
                    log.warning('PostMessage截图失败，尝试回退到PC控制器')
            except Exception as e:
                log.warning(f'PostMessage截图异常: {e}，尝试回退到PC控制器')
                self._post_message_available = False

        # 回退到PC控制器截图
        return PcControllerBase.get_screenshot(self, independent)

    def mouse_move(self, game_pos: Point):
        """
        鼠标移动到指定的位置 - 优先使用PostMessage
        :param game_pos: 游戏坐标系中的位置
        """
        if self._post_message_available:
            try:
                self.post_message_controller.mouse_move(game_pos)
                return
            except Exception as e:
                log.warning(f'PostMessage鼠标移动异常: {e}，尝试回退到PC控制器')
                self._post_message_available = False

        # 回退到PC控制器
        PcControllerBase.mouse_move(self, game_pos)

    def close_game(self):
        """
        关闭游戏 - 优先使用PostMessage
        """
        if self._post_message_available:
            try:
                self.post_message_controller.close_game()
                return
            except Exception as e:
                log.warning(f'PostMessage关闭游戏异常: {e}，尝试回退到PC控制器')
                self._post_message_available = False

        # 回退到PC控制器
        PcControllerBase.close_game(self)

    def active_window(self) -> None:
        """
        前置窗口 - 使用PC控制器的方法（更可靠）
        """
        PcControllerBase.active_window(self)
        # 同时更新PostMessage控制器的窗口状态
        if self._post_message_available:
            try:
                self.post_message_controller.active_window()
            except Exception as e:
                log.warning(f'PostMessage前置窗口异常: {e}')

    @property
    def is_using_post_message(self) -> bool:
        """
        是否正在使用PostMessage
        :return: 是否使用PostMessage
        """
        return self._post_message_available

    def force_use_pc_controller(self):
        """
        强制使用PC控制器
        """
        self._post_message_available = False
        log.info('已强制切换到PC控制器模式')

    def try_enable_post_message(self):
        """
        尝试重新启用PostMessage
        """
        try:
            if self.post_message_controller.init_before_context_run():
                self._post_message_available = True
                log.info('PostMessage控制器已重新启用')
                return True
        except Exception as e:
            log.warning(f'重新启用PostMessage失败: {e}')
        
        return False

    def get_controller_status(self) -> str:
        """
        获取控制器状态信息
        :return: 状态字符串
        """
        if self._post_message_available:
            return "混合控制器 - PostMessage模式"
        else:
            return "混合控制器 - PC控制器模式"
