from enum import Enum
from typing import Optional

import keyboard
import pyautogui

from one_dragon.base.controller.controller_base import ControllerBase
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.matcher.ocr_matcher import OcrMatcher
from one_dragon.base.matcher.template_matcher import TemplateMatcher
from one_dragon.base.operation.context_event_bus import ContextEventBus
from one_dragon.utils import debug_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


class ContextRunStateEnum(Enum):

    STOP: int = 0  # 停止
    RUN: int = 1  # 正在运行
    PAUSE: int = 2  # 暂停


class ContextRunningStateEventEnum(Enum):
    """
    运行状态相关的事件 事件体为 ContextRunStateEnum
    """

    START_RUNNING: str = 'context_start_running'
    PAUSE_RUNNING: str = 'context_pause_running'
    RESUME_RUNNING: str = 'context_resume_running'
    STOP_RUNNING: str = 'context_stop_running'


class ContextKeyboardEventEnum(Enum):

    PRESS: str = 'context_keyboard_press'


class ContextBase(ContextEventBus):

    def __init__(self, controller: Optional[ControllerBase] = None
                 ):
        ContextEventBus.__init__(self)

        self.context_running_state: ContextRunStateEnum = ContextRunStateEnum.STOP

        self.tm: TemplateMatcher = TemplateMatcher()
        self.ocr: OcrMatcher = OcrMatcher()
        self.controller: ControllerBase = controller
        keyboard.on_press(self.__on_key_press)

    def start_running(self) -> bool:
        """
        开始运行
        :return:
        """
        if self.context_running_state != ContextRunStateEnum.STOP:
            log.error('请先结束其他运行中的功能 再启动')
            return False

        self.context_running_state = ContextRunStateEnum.RUN
        self.controller.init()
        self.dispatch_event(ContextRunningStateEventEnum.START_RUNNING.value, self.context_running_state)
        return True

    def stop_running(self):
        if self.is_context_running:  # 先触发暂停 让执行中的指令停止
            self.switch_context_pause_and_run()
        self.context_running_state = ContextRunStateEnum.STOP
        log.info('停止运行')
        self.dispatch_event(ContextRunningStateEventEnum.STOP_RUNNING.value, self.context_running_state)

    @property
    def is_context_stop(self) -> bool:
        return self.context_running_state == ContextRunStateEnum.STOP

    @property
    def is_context_running(self) -> bool:
        return self.context_running_state == ContextRunStateEnum.RUN

    @property
    def is_context_pause(self) -> bool:
        return self.context_running_state == ContextRunStateEnum.PAUSE

    @property
    def context_running_status_text(self) -> str:
        if self.context_running_state == ContextRunStateEnum.STOP:
            return gt('空闲', 'ui')
        elif self.context_running_state == ContextRunStateEnum.RUN:
            return gt('运行中', 'ui')
        elif self.context_running_state == ContextRunStateEnum.PAUSE:
            return gt('暂停中', 'ui')
        else:
            return 'unknow'

    def switch_context_pause_and_run(self):
        if self.context_running_state == ContextRunStateEnum.RUN:
            log.info('暂停运行')
            self.context_running_state = ContextRunStateEnum.PAUSE
            self.dispatch_event(ContextRunningStateEventEnum.PAUSE_RUNNING.value, self.context_running_state)
        elif self.context_running_state == ContextRunStateEnum.PAUSE:
            log.info('恢复运行')
            self.context_running_state = ContextRunStateEnum.RUN
            self.dispatch_event(ContextRunningStateEventEnum.RESUME_RUNNING.value, self.context_running_state)

    def __on_key_press(self, event):
        """
        按键时触发 抛出事件，事件体为按键
        :param event:
        :return:
        """
        k = event.name

        if k == self.key_start_running:
            self.switch_context_pause_and_run()
        elif k == self.key_stop_running:
            self.stop_running()
        elif k == self.key_screenshot:
            self.screenshot_and_save_debug()
        elif k == self.key_mouse_pos:
            self.log_mouse_position()

        self.dispatch_event(ContextKeyboardEventEnum.PRESS.value, k)

    @property
    def is_game_window_ready(self) -> bool:
        """
        游戏窗口是否已经出现
        :return:
        """
        return self.controller.is_game_window_ready

    @property
    def key_start_running(self) -> str:
        return 'f9'

    @property
    def key_stop_running(self) -> str:
        return 'f10'

    @property
    def key_screenshot(self) -> str:
        return 'f11'

    @property
    def key_mouse_pos(self) -> str:
        return 'f12'

    def screenshot_and_save_debug(self) -> None:
        """
        截图 保存到debug
        """
        if self.controller is None or not self.controller.is_game_window_ready:
            return
        self.controller.init()
        img = self.controller.screenshot()
        debug_utils.save_debug_image(img)

    def log_mouse_position(self):
        if self.controller is None or not self.controller.is_game_window_ready:
            return

        rect: Rect = self.controller.game_win.win_rect
        pos = pyautogui.position()
        log.info('当前鼠标坐标 %s', (pos.x - rect.x1, pos.y - rect.y1))
