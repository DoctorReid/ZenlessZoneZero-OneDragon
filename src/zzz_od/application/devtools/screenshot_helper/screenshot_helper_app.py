import time

from typing import Optional

from one_dragon.base.operation.context_event_bus import ContextEventItem
from one_dragon.base.operation.one_dragon_context import ContextKeyboardEventEnum
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_node import OperationNode
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import debug_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
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
        self.auto_op: Optional[AutoBattleOperator] = None
        self.screenshot_cache: list = []  # 缓存所有截图
        self.cache_start_time: Optional[float] = None  # 缓存开始时间
        self.cache_max_count: int = 0  # 最大缓存数量
        self.is_saving_after_key: bool = False  # 是否正在保存按键后的截图

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
        length_second = self.ctx.screenshot_helper_config.length_second
        freq_second = self.ctx.screenshot_helper_config.frequency_second
        self.ctx.controller.screenshot_alive_seconds = length_second + 1
        self.ctx.controller.max_screenshot_cnt = length_second // freq_second + 5
        self.cache_max_count = length_second // freq_second + 1
        self.screenshot_cache = []
        self.cache_start_time = time.time()
        self.ctx.listen_event(ContextKeyboardEventEnum.PRESS.value, self._on_key_press)

    def init_context(self) -> OperationRoundResult:
        auto_battle_utils.load_auto_op(self, 'dodge',
                                       self.ctx.battle_assistant_config.dodge_assistant_config)
        return self.round_success()

    def repeat_screenshot(self) -> OperationRoundResult:
        """
        持续截图
        """
        now = time.time()
        screen = self.screenshot()

        # 缓存截图
        if self.cache_start_time is None:
            self.cache_start_time = now
        self.screenshot_cache.append(screen)
        # 动态计算最大缓存数量
        if len(self.screenshot_cache) > self.cache_max_count:
            self.screenshot_cache.pop(0)

        if self.ctx.screenshot_helper_config.dodge_detect:
            if self.auto_op.auto_battle_context.dodge_context.check_dodge_flash(screen, now):
                debug_utils.save_debug_image(screen, prefix='dodge')
            elif self.auto_op.auto_battle_context.dodge_context.check_dodge_audio(now):
                debug_utils.save_debug_image(screen, prefix='dodge')

        if self.to_save_screenshot:
            if not self.ctx.screenshot_helper_config.screenshot_before_key and self.is_saving_after_key:
                # 在按键后截图模式下，保存当前截图
                debug_utils.save_debug_image(screen, prefix='switch')
            return self.round_success()
        else:
            # 确保每次截图间隔正确
            next_time = self.ctx.screenshot_helper_config.frequency_second - (time.time() - now)
            return self.round_wait(wait_round_time=max(0.01, next_time))

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
        if self.ctx.screenshot_helper_config.screenshot_before_key:
            # 保存缓存中的截图
            for screen in self.screenshot_cache:
                debug_utils.save_debug_image(screen, prefix='switch')
            self.screenshot_cache = []
            self.cache_start_time = time.time()
            self.to_save_screenshot = False
            self.last_save_screenshot_time = time.time()
        else:
            # 清空缓存并开始保存按键后的截图
            self.screenshot_cache = []
            self.cache_start_time = time.time()
            self.is_saving_after_key = True
            # 等待一个截图周期后再关闭保存标志，以确保能够捕获按键后的截图
            next_time = self.ctx.screenshot_helper_config.frequency_second
            return self.round_wait(wait_round_time=next_time)
        return self.round_success()

    def after_operation_done(self, result: OperationResult):
        ZApplication.after_operation_done(self, result)

        self.ctx.controller.max_screenshot_cnt = 0
