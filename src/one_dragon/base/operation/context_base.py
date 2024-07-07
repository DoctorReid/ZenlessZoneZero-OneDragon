from enum import Enum
from typing import Optional

import keyboard

from one_dragon.base.controller.controller_base import ControllerBase
from one_dragon.base.matcher.ocr_matcher import OcrMatcher
from one_dragon.base.matcher.template_matcher import TemplateMatcher
from one_dragon.base.operation.context_event_bus import ContextEventBus
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


class ContextRunStateEnum(Enum):

    STOP: int = 0  # 停止
    RUN: int = 1  # 正在运行
    PAUSE: int = 2  # 暂停


class ContextEventEnum(Enum):

    START_RUNNING: str = 'context_start_running'
    PAUSE_RUNNING: str = 'context_pause_running'
    RESUME_RUNNING: str = 'context_resume_running'
    STOP_RUNNING: str = 'context_stop_running'


class ContextKeyboardEventEnum(Enum):

    PRESS: str = 'context_keyboard_press'


class ContextBase(ContextEventBus):

    def __init__(self, controller: Optional[ControllerBase] = None):
        ContextEventBus.__init__(self)

        self.context_running_state: int = ContextRunStateEnum.STOP.value

        self.tm: TemplateMatcher = TemplateMatcher()
        self.ocr: OcrMatcher = OcrMatcher()
        self.controller: ControllerBase = controller

        keyboard.on_press(self.__on_key_press)

    def start_running(self) -> bool:
        """
        开始运行
        :return:
        """
        if self.context_running_state != ContextRunStateEnum.STOP.value:
            log.error('请先结束其他运行中的功能 再启动')
            return False

        self.context_running_state = ContextRunStateEnum.RUN.value
        self.dispatch_event(ContextEventEnum.START_RUNNING.value)
        return True

    def stop_running(self):
        if self.is_context_running:  # 先触发暂停 让执行中的指令停止
            self.switch_context_pause_and_run()
        self.context_running_state = ContextRunStateEnum.STOP.value
        log.info('停止运行')
        self.dispatch_event(ContextEventEnum.STOP_RUNNING.value)

    @property
    def is_context_stop(self) -> bool:
        return self.context_running_state == ContextRunStateEnum.STOP.value

    @property
    def is_context_running(self) -> bool:
        return self.context_running_state == ContextRunStateEnum.RUN.value

    @property
    def is_context_pause(self) -> bool:
        return self.context_running_state == ContextRunStateEnum.PAUSE.value

    @property
    def context_running_status_text(self) -> str:
        if self.context_running_state == 0:
            return gt('空闲', 'ui')
        elif self.context_running_state == 1:
            return gt('运行中', 'ui')
        elif self.context_running_state == 2:
            return gt('暂停中', 'ui')
        else:
            return 'unknow'

    def switch_context_pause_and_run(self):
        if self.context_running_state == ContextRunStateEnum.RUN.value:
            log.info('暂停运行')
            self.context_running_state = ContextRunStateEnum.PAUSE.value
            self.dispatch_event(ContextEventEnum.PAUSE_RUNNING.value)
        elif self.context_running_state == ContextRunStateEnum.PAUSE.value:
            log.info('恢复运行')
            self.context_running_state = ContextRunStateEnum.RUN.value
            self.dispatch_event(ContextEventEnum.RESUME_RUNNING.value)

    def __on_key_press(self, event):
        """
        按键时触发 抛出事件，事件体为按键
        :param event:
        :return:
        """
        k = event.name
        self.dispatch_event(ContextKeyboardEventEnum.PRESS.value, k)

    @property
    def is_game_window_ready(self) -> bool:
        """
        游戏窗口是否已经出现
        :return:
        """
        return self.controller.is_game_window_ready
