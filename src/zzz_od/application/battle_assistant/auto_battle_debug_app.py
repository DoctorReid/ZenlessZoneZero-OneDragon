import time

from typing import Optional

from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.conditional_operation.operation_task import OperationTask
from one_dragon.base.controller.pc_button import pc_button_utils
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_node import OperationNode
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.battle_assistant.auto_battle_app import AutoBattleApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.config.game_config import GamepadTypeEnum
from zzz_od.context.zzz_context import ZContext


class AutoBattleDebugApp(ZApplication):

    def __init__(self, ctx: ZContext):
        """
        识别后进行闪避
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='auto_battle_debug',
            op_name=gt('自动战斗调试', 'ui'),
            need_ocr=False
        )

        self.auto_op: Optional[ConditionalOperator] = None

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check_gamepad = OperationNode('手柄检测', self.check_gamepad)

        load_op = OperationNode('加载自动战斗指令', self.load_op)
        self.add_edge(check_gamepad, load_op)

        init_context = OperationNode('初始化上下文', self.init_context)
        self.add_edge(load_op, init_context)

        check = OperationNode('画面识别', self.check_screen)
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
        self.ctx.battle_dodge.init_dodge_model(use_gpu=self.ctx.battle_assistant_config.use_gpu)
        return self.round_success()

    def load_op(self) -> OperationRoundResult:
        """
        加载战斗指令
        :return:
        """
        result = auto_battle_utils.load_auto_op(self, 'auto_battle',
                                                self.ctx.battle_assistant_config.auto_battle_config)

        if result.is_success:
            self.ctx.dispatch_event(
                AutoBattleApp.EVENT_OP_LOADED,
                self.auto_op.get_usage_states(),
            )

        return result

    def init_context(self) -> OperationRoundResult:
        """
        初始初始化上下文
        :return:
        """
        auto_battle_utils.init_context(self)

        return self.round_success()

    def check_screen(self) -> OperationRoundResult:
        """
        识别当前画面 并进行点击
        :return:
        """
        now = time.time()

        screen = self.screenshot()
        auto_battle_utils.run_screen_check(self, screen, now, sync=True)

        time.sleep(0.2)
        ops = self.auto_op._normal_scene_handler.get_operations(time.time())
        if ops is not None:
            task = OperationTask(False, ops)
            task.run_async().result()

        return self.round_success()

    def _on_pause(self, e=None):
        ZApplication._on_pause(self, e)
        auto_battle_utils.stop_running(self)

    def _on_resume(self, e=None):
        ZApplication._on_resume(self, e)
        auto_battle_utils.resume_running(self)

    def _after_operation_done(self, result: OperationResult):
        ZApplication._after_operation_done(self, result)
        auto_battle_utils.stop_running(self)
        if self.auto_op is not None:
            self.auto_op.dispose()
            self.auto_op = None
