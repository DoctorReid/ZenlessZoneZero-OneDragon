import time

from typing import Optional

from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.operation.context_event_bus import ContextEventItem
from one_dragon.base.operation.one_dragon_context import ContextKeyboardEventEnum
from one_dragon.base.operation.operation import OperationNode, OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle.auto_battle_loader import AutoBattleLoader
from zzz_od.context.zzz_context import ZContext


class DodgeAssistantApp(ZApplication):

    def __init__(self, ctx: ZContext):
        """
        按闪避的时候自动截图 用于保存素材训练模型
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='dodge_assistant',
            op_name=gt('闪避助手', 'ui')
        )

        self.auto_op: Optional[ConditionalOperator] = None

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        load_model = OperationNode('加载判断模型', self.load_model)
        load_op = OperationNode('加载闪避指令', self.load_op)
        self.add_edge(load_model, load_op)

        check = OperationNode('闪避判断', self.check_dodge)
        self.add_edge(load_op, check)

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        pass

    def load_op(self) -> OperationRoundResult:
        """
        加载战斗指令
        :return:
        """
        if self.auto_op is not None:  # 如果有上一个 先销毁
            self.auto_op.dispose()
        auto_battle_loader = AutoBattleLoader(self.ctx)
        self.auto_op = ConditionalOperator(module_name=self.ctx.dodge_assistant_config.dodge_way, sub_dir='dodge')
        self.auto_op.init(event_bus=self.ctx,
                          state_recorders=auto_battle_loader.get_all_state_recorders(),
                          op_constructor=auto_battle_loader.get_atomic_op)
        self.auto_op.start_running_async()
        return self.round_success()

    def load_model(self) -> OperationRoundResult:
        """
        加载模型
        :return:
        """
        self.ctx.init_dodge_model(use_gpu=self.ctx.dodge_assistant_config.use_gpu)
        return self.round_success()

    def check_dodge(self) -> OperationRoundResult:
        """
        识别当前画面 并进行点击
        :return:
        """
        now = time.time()

        screen = self.screenshot()
        self.ctx.should_dodge(screen, now, self.ctx.dodge_assistant_config.use_gpu)

        return self.round_wait(wait_round_time=self.ctx.dodge_assistant_config.screenshot_interval)

    def _on_pause(self, e=None):
        ZApplication._on_pause(self, e)
        if self.auto_op is not None:
            self.auto_op.stop_running()

    def _on_resume(self, e=None):
        ZApplication._on_resume(self, e)
        if self.auto_op is not None:
            self.auto_op.start_running_async()
