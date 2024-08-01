import time

from one_dragon.base.operation.context_event_bus import ContextEventItem
from one_dragon.base.operation.one_dragon_context import ContextKeyboardEventEnum
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.base.operation.operation_node import OperationNode
from one_dragon.utils import debug_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext


class ScreenshotHelperApp(ZApplication):

    def __init__(self, ctx: ZContext):
        """
        按闪避的时候自动截图 用于保存素材训练模型
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='screenshot_helper',
            op_name=gt('闪避截图', 'ui')
        )

        self.to_save_screenshot: bool = False  # 去保存截图 由按键触发
        self.last_save_screenshot_time: float = 0  # 上次保存截图时间

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        init_context = OperationNode('初始化上下文', self.init_context)

        screenshot = OperationNode('持续截图', self.repeat_screenshot)
        self.add_edge(init_context, screenshot)

        save = OperationNode('保存截图', self.do_save_screenshot)
        self.add_edge(screenshot, save)
        self.add_edge(save, screenshot)

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        self.ctx.controller.screenshot_alive_seconds = self.ctx.screenshot_helper_config.length_second + 1
        self.ctx.controller.max_screenshot_cnt = self.ctx.screenshot_helper_config.length_second // self.ctx.screenshot_helper_config.frequency_second + 5

        self.ctx.listen_event(ContextKeyboardEventEnum.PRESS.value, self._on_key_press)

    def init_context(self) -> OperationRoundResult:
        self.ctx.yolo.init_context(self.ctx.battle_assistant_config.use_gpu)
        return self.round_success()

    def repeat_screenshot(self) -> OperationRoundResult:
        """
        持续截图
        """
        now = time.time()
        screen = self.screenshot()

        if self.ctx.screenshot_helper_config.dodge_detect:
            if self.ctx.yolo.check_dodge_flash(screen, now):
                debug_utils.save_debug_image(screen, prefix='dodge_wrong')

        if self.to_save_screenshot:
            return self.round_success()
        else:
            return self.round_wait(wait_round_time=self.ctx.screenshot_helper_config.frequency_second)

    def _on_key_press(self, event: ContextEventItem) -> None:
        """
        按键监听
        """
        if self.to_save_screenshot:  # 上轮截图还没有完成保存
            return
        key: str = event.data
        if time.time() - self.last_save_screenshot_time <= 1:  # 每秒最多保持一次 防止战斗中按得太多
            return
        if key != self.ctx.screenshot_helper_config.key_save:
            return

        self.to_save_screenshot = True

    def do_save_screenshot(self) -> OperationRoundResult:
        """
        保存截图
        """
        screen_history = self.ctx.controller.screenshot_history.copy()
        for screen in screen_history:
            debug_utils.save_debug_image(screen.image, prefix='switch')

        self.to_save_screenshot = False
        self.last_save_screenshot_time = time.time()

        return self.round_success()
