from typing import Optional
from cv2.typing import MatLike

from one_dragon.base.controller.pc_controller_base import PcControllerBase
from one_dragon.base.controller.post_message_controller import PostMessageController
from one_dragon.utils.log_utils import log


class ScreenshotHybridController(PcControllerBase):
    """
    截图混合控制器 - 截图使用PostMessage，其他功能使用PC控制器
    继承PcControllerBase，仅截图方法集成PostMessageController功能
    """

    def __init__(self, win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        """
        初始化截图混合控制器
        :param win_title: 目标窗口标题
        :param standard_width: 标准宽度
        :param standard_height: 标准高度
        """
        # 初始化基础PC控制器
        PcControllerBase.__init__(self, win_title, standard_width, standard_height)
        
        # 初始化PostMessage控制器用于截图
        self.post_message_controller = PostMessageController(
            win_title=win_title,
            standard_width=standard_width,
            standard_height=standard_height
        )
        
        # 标记PostMessage截图是否可用
        self._post_message_screenshot_available = True

    def init_before_context_run(self) -> bool:
        """运行前初始化"""
        # 首先尝试初始化PostMessage控制器
        post_msg_success = self.post_message_controller.init_before_context_run()
        if not post_msg_success:
            log.warning('PostMessage控制器初始化失败，截图将回退到PC控制器')
            self._post_message_screenshot_available = False
        
        # 初始化基础PC控制器
        pc_success = PcControllerBase.init_before_context_run(self)
        
        return pc_success

    def get_screenshot(self, independent: bool = False) -> MatLike:
        """
        截图 - 优先使用PostMessage的后台截图功能
        :param independent: 是否独立截图
        :return: 截图
        """
        if self._post_message_screenshot_available:
            try:
                screenshot = self.post_message_controller.get_screenshot(independent)
                if screenshot is not None:
                    return screenshot
                else:
                    log.warning('PostMessage截图失败，尝试回退到PC控制器')
            except Exception as e:
                log.warning(f'PostMessage截图异常: {e}，尝试回退到PC控制器')
                self._post_message_screenshot_available = False

        # 回退到PC控制器截图
        return PcControllerBase.get_screenshot(self, independent)

    @property
    def is_using_post_message_screenshot(self) -> bool:
        """
        是否正在使用PostMessage截图
        :return: 是否使用PostMessage截图
        """
        return self._post_message_screenshot_available

    def force_use_pc_screenshot(self):
        """
        强制使用PC控制器截图
        """
        self._post_message_screenshot_available = False
        log.info('已强制切换到PC控制器截图模式')

    def try_enable_post_message_screenshot(self):
        """
        尝试重新启用PostMessage截图
        """
        try:
            if self.post_message_controller.init_before_context_run():
                self._post_message_screenshot_available = True
                log.info('PostMessage截图功能已重新启用')
                return True
        except Exception as e:
            log.warning(f'重新启用PostMessage截图失败: {e}')
        
        return False

    def get_controller_status(self) -> str:
        """
        获取控制器状态信息
        :return: 状态字符串
        """
        if self._post_message_screenshot_available:
            return "截图混合控制器 - PostMessage截图模式"
        else:
            return "截图混合控制器 - PC控制器截图模式"
