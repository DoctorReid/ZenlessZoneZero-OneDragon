import logging
from enum import Enum
from pynput import keyboard, mouse
from typing import Optional

from one_dragon.base.config.one_dragon_config import OneDragonConfig
from one_dragon.base.controller.controller_base import ControllerBase
from one_dragon.base.controller.pc_button.pc_button_listener import PcButtonListener
from one_dragon.base.matcher.ocr.ocr_matcher import OcrMatcher
from one_dragon.base.matcher.ocr.onnx_ocr_matcher import OnnxOcrMatcher
from one_dragon.base.matcher.template_matcher import TemplateMatcher
from one_dragon.base.operation.context_event_bus import ContextEventBus
from one_dragon.base.screen.screen_loader import ScreenLoader
from one_dragon.base.screen.template_loader import TemplateLoader
from one_dragon.envs.env_config import EnvConfig
from one_dragon.envs.git_service import GitService
from one_dragon.envs.project_config import ProjectConfig
from one_dragon.envs.python_service import PythonService
from one_dragon.utils import debug_utils, log_utils
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


class OneDragonContext(ContextEventBus):

    def __init__(self, controller: Optional[ControllerBase] = None):
        ContextEventBus.__init__(self)
        self.project_config: ProjectConfig = ProjectConfig()
        self.env_config: EnvConfig = EnvConfig()
        self.one_dragon_config: OneDragonConfig = OneDragonConfig()

        self.git_service: GitService = GitService(self.project_config, self.env_config)
        self.python_service: PythonService = PythonService(self.project_config, self.env_config, self.git_service)

        self.context_running_state: ContextRunStateEnum = ContextRunStateEnum.STOP

        self.screen_loader: ScreenLoader = ScreenLoader()
        self.template_loader: TemplateLoader = TemplateLoader()
        self.tm: TemplateMatcher = TemplateMatcher(self.template_loader)
        self.ocr: OcrMatcher = OnnxOcrMatcher()
        self.controller: ControllerBase = controller

        self.keyboard_controller = keyboard.Controller()
        self.mouse_controller = mouse.Controller()
        self.btn_listener = PcButtonListener(on_button_tap=self._on_key_press, listen_keyboard=True)
        self.btn_listener.start()

    def init_by_config(self) -> None:
        """
        根据配置进行初始化
        不能在 __init__ 中调用，因为子类可能还没有完成初始话
        :return:
        """
        log_utils.set_log_level(logging.DEBUG if self.env_config.is_debug else logging.INFO)

    def start_running(self) -> bool:
        """
        开始运行
        :return:
        """
        if self.context_running_state != ContextRunStateEnum.STOP:
            log.error('请先结束其他运行中的功能 再启动')
            return False

        self.context_running_state = ContextRunStateEnum.RUN
        self.controller.init_before_context_run()
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

    def _on_key_press(self, key: str):
        """
        按键时触发 抛出事件，事件体为按键
        :param key: 按键
        :return:
        """
        if key == self.key_start_running:
            self.switch_context_pause_and_run()
        elif key == self.key_stop_running:
            self.stop_running()
        elif key == self.key_screenshot:
            self.screenshot_and_save_debug()

        self.dispatch_event(ContextKeyboardEventEnum.PRESS.value, key)

    @property
    def is_game_window_ready(self) -> bool:
        """
        游戏窗口是否已经出现
        :return:
        """
        return self.controller.is_game_window_ready

    @property
    def key_start_running(self) -> str:
        return self.env_config.key_start_running

    @property
    def key_stop_running(self) -> str:
        return self.env_config.key_stop_running

    @property
    def key_screenshot(self) -> str:
        return self.env_config.key_screenshot

    @property
    def key_debug(self) -> str:
        return self.env_config.key_debug

    def screenshot_and_save_debug(self) -> None:
        """
        截图 保存到debug
        """
        if self.controller is None or not self.controller.is_game_window_ready:
            return
        self.controller.init_before_context_run()
        img = self.controller.screenshot()
        debug_utils.save_debug_image(img)
