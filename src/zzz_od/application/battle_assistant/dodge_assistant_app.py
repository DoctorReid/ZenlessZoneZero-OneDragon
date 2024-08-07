import time

from typing import Optional

from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.controller.pc_button import pc_button_utils
from one_dragon.base.operation.operation_node import OperationNode
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.battle_assistant.auto_battle_app import AutoBattleApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.config.game_config import GamepadTypeEnum
from zzz_od.context.zzz_context import ZContext


class DodgeAssistantApp(ZApplication):

    def __init__(self, ctx: ZContext):
        """
        识别后进行闪避
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='dodge_assistant',
            op_name=gt('闪避助手', 'ui'),
            need_ocr=False
        )

        self.auto_op: Optional[ConditionalOperator] = None

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check_gamepad = OperationNode('手柄检测', self.check_gamepad)

        load_op = OperationNode('加载闪避指令', self.load_op)
        self.add_edge(check_gamepad, load_op)

        init_context = OperationNode('初始化上下文', self.init_context)
        self.add_edge(load_op, init_context)

        check = OperationNode('闪避判断', self.check_dodge)
        self.add_edge(init_context, check)

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        pass

    def check_gamepad(self) -> OperationRoundResult:
        """
        检测手柄
        :return:
        """
        if self.ctx.battle_assistant_config.gamepad_type == GamepadTypeEnum.NONE.value.value:
            self.ctx.controller.enable_keyboard()
            return self.round_success(status='无需手柄')
        elif not pc_button_utils.is_vgamepad_installed():
            self.ctx.controller.enable_keyboard()
            return self.round_fail(status='未安装虚拟手柄依赖')
        elif self.ctx.battle_assistant_config.gamepad_type == GamepadTypeEnum.XBOX.value.value:
            self.ctx.controller.enable_xbox()
            self.ctx.controller.btn_controller.set_key_press_time(self.ctx.game_config.xbox_key_press_time)
        elif self.ctx.battle_assistant_config.gamepad_type == GamepadTypeEnum.DS4.value.value:
            self.ctx.controller.enable_ds4()
            self.ctx.controller.btn_controller.set_key_press_time(self.ctx.game_config.ds4_key_press_time)
        return self.round_success(status='已安装虚拟手柄依赖')

    def load_model(self) -> OperationRoundResult:
        """
        加载模型
        :return:
        """
        self.ctx.yolo.init_context(use_gpu=self.ctx.battle_assistant_config.use_gpu)
        return self.round_success()

    def load_op(self) -> OperationRoundResult:
        """
        加载战斗指令
        :return:
        """
        result = auto_battle_utils.load_auto_op(self, 'dodge',
                                                self.ctx.battle_assistant_config.dodge_assistant_config)

        if result.is_success:
            self.ctx.dispatch_event(
                AutoBattleApp.EVENT_OP_LOADED,
                self.auto_op.get_usage_states(),
            )
            self.auto_op.start_running_async()

        return result

    def init_context(self) -> OperationRoundResult:
        """
        初始初始化上下文
        :return:
        """
        auto_battle_utils.init_context(self)

        return self.round_success()

    def check_dodge(self) -> OperationRoundResult:
        """
        识别当前画面 并进行点击
        :return:
        """
        now = time.time()

        screen = self.screenshot()
        auto_battle_utils.run_screen_check(self, screen, now, check_battle_end=False)

        return self.round_wait(wait_round_time=self.ctx.battle_assistant_config.screenshot_interval)

    def _on_pause(self, e=None):
        ZApplication._on_pause(self, e)
        if self.auto_op is not None:
            self.auto_op.stop_running()

    def _on_resume(self, e=None):
        ZApplication._on_resume(self, e)
        if self.auto_op is not None:
            self.auto_op.start_running_async()
