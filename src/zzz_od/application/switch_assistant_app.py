import time

from one_dragon.base.operation.context_base import ContextKeyboardEventEnum
from one_dragon.base.operation.operation import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext


class ScreenshotSwitchApp(ZApplication):

    def __init__(self, ctx: ZContext):
        """
        按闪避的时候自动截图 用于保存素材训练模型
        """
        ZApplication.__init__(
            self,
            ctx=ctx,
            op_name=gt('辅助闪避', 'ui')
        )

        self.last_switch_time: float = time.time()

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        self.ctx.listen_event(ContextKeyboardEventEnum.PRESS.value, self._on_key_press)

    def _on_key_press(self, key: str) -> None:
        """
        监听按键触发
        :param key:
        :return:
        """
        if key not in [
            self.ctx.game_config.key_change_next,
            self.ctx.game_config.key_change_prev
        ]:
            return
        self.last_switch_time = time.time()  # 更新按键时间

    def help_switch(self) -> OperationRoundResult:
        """
        识别当前画面 并进行点击
        :return:
        """
        now = time.time()
        if now - self.last_switch_time <= 1:  # 短时间内只要闪避一次就够了
            return self.round_wait(wait_round_time=now - self.last_switch_time)

        screen = self.screenshot()
        if self.ctx.should_switch(screen):
            self.last_switch_time = time.time()
            self.ctx.controller.switch_next()

        return self.round_wait()
