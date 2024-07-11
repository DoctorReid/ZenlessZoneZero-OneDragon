import time

from one_dragon.base.operation.context_base import ContextKeyboardEventEnum
from one_dragon.base.operation.operation import OperationNode, OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.dodge_assistant.dodge_assistant_config import DodgeWayEnum
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext


class DodgeAssistantApp(ZApplication):

    def __init__(self, ctx: ZContext):
        """
        按闪避的时候自动截图 用于保存素材训练模型
        """
        ZApplication.__init__(
            self,
            ctx=ctx,
            op_name=gt('辅助闪避', 'ui')
        )

        self.last_dodge_time: float = time.time()

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check = OperationNode('闪避判断', self.check_dodge)
        self.param_start_node = check

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
            self.ctx.game_config.key_switch_next,
            self.ctx.game_config.key_switch_prev,
            self.ctx.game_config.key_dodge
        ]:
            return
        self.last_dodge_time = time.time()  # 更新按键时间

    def check_dodge(self) -> OperationRoundResult:
        """
        识别当前画面 并进行点击
        :return:
        """
        now = time.time()
        if now - self.last_dodge_time <= 1:  # 短时间内只要闪避一次就够了
            return self.round_wait(wait_round_time=now - self.last_dodge_time)

        screen = self.screenshot()
        if self.ctx.should_dodge(screen):
            self.last_dodge_time = time.time()
            if self.ctx.dodge_assistant_config.dodge_way == DodgeWayEnum.DODGE.value.value:
                self.ctx.controller.dodge()
            elif self.ctx.dodge_assistant_config.dodge_way == DodgeWayEnum.NEXT.value.value:
                self.ctx.controller.switch_next()
            elif self.ctx.dodge_assistant_config.dodge_way == DodgeWayEnum.PREV.value.value:
                self.ctx.controller.switch_prev()

        return self.round_wait()
