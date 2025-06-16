import time

from typing import Optional, List

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.utils import get_ops_by_template
from one_dragon.base.controller.pc_button import pc_button_utils
from one_dragon.base.operation.operation_node import OperationNode
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.config.game_config import GamepadTypeEnum
from zzz_od.context.zzz_context import ZContext


class OperationDebugApp(ZApplication):

    def __init__(self, ctx: ZContext):
        """
        识别后进行闪避
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='auto_battle',
            op_name=gt('指令调试'),
            need_ocr=False
        )

        self.ops: Optional[List[AtomicOp]] = None
        self.op_idx: int = 0

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check_gamepad = OperationNode('手柄检测', self.check_gamepad)

        load_op = OperationNode('加载动作指令', self.load_op)
        self.add_edge(check_gamepad, load_op)

        init_context = OperationNode('初始化上下文', self.init_context)
        self.add_edge(load_op, init_context)

        run_operations = OperationNode('执行指令', self.run_operations)
        self.add_edge(init_context, run_operations)

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

    def load_op(self) -> OperationRoundResult:
        """
        加载战斗指令
        :return:
        """
        op = AutoBattleOperator(self.ctx, '', '', is_mock=True)
        template_name = self.ctx.battle_assistant_config.debug_operation_config
        operation_template = AutoBattleOperator.get_operation_template(template_name)
        if operation_template is None:
            return self.round_fail('无效的自动战斗指令 请重新选择')

        try:
            self.ops = get_ops_by_template(
                template_name,
                op.get_atomic_op,
                AutoBattleOperator.get_operation_template,
                set()
            )
            self.op_idx = 0
            return self.round_success()
        except Exception:
            log.error('指令模板加载失败', exc_info=True)
            return self.round_fail()

    def init_context(self) -> OperationRoundResult:
        """
        初始初始化上下文
        :return:
        """
        return self.round_success()

    def run_operations(self) -> OperationRoundResult:
        """
        执行指令
        :return:
        """
        now = time.time()

        self.ops[self.op_idx].execute()
        self.op_idx += 1
        if self.op_idx >= len(self.ops):
            if self.ctx.battle_assistant_config.debug_operation_repeat:
                self.op_idx = 0
                return self.round_wait()
            else:
                return self.round_success()
        else:
            return self.round_wait()

    def _on_pause(self, e=None):
        ZApplication._on_pause(self, e)

    def _on_resume(self, e=None):
        ZApplication._on_resume(self, e)
