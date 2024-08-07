from cv2.typing import MatLike
from typing import Union

from one_dragon.base.operation.operation_round_result import OperationRoundResult
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.operation.zzz_operation import ZOperation


def load_auto_op(op: Union[ZOperation, ZApplication], auto_config_sub_dir: str, auto_config_name: str) -> OperationRoundResult:
    """
    加载自动战斗指令
    :param op:
    :param auto_config_sub_dir:
    :param auto_config_name:
    :return:
    """
    if op.auto_op is not None:  # 如果有上一个 先销毁
        op.auto_op.dispose()
    op.auto_op = AutoBattleOperator(op.ctx, auto_config_sub_dir, auto_config_name)
    if not op.auto_op.is_file_exists():
        return op.round_fail('无效的自动战斗指令 请重新选择')

    op.auto_op.init_operator()

    return op.round_success()


def init_context(op: Union[ZOperation, ZApplication]):
    """
    初始化上下文
    :param op:
    :return:
    """
    op.ctx.yolo.init_context(
        use_gpu=op.ctx.battle_assistant_config.use_gpu,
        check_dodge_interval=op.auto_op.get('check_dodge_interval', 0.02),
    )
    op.ctx.battle.init_context(
        check_agent_interval=op.auto_op.get('check_agent_interval', 0.5),
        check_special_attack_interval=op.auto_op.get('check_special_attack_interval', 0.5),
        check_ultimate_interval=op.auto_op.get('check_ultimate_interval', 0.5),
        check_chain_interval=op.auto_op.get('check_chain_interval', 1),
        check_quick_interval=op.auto_op.get('check_quick_interval', 0.5),
        check_end_interval=op.auto_op.get('check_end_interval', 5),

        allow_ultimate_list=op.auto_op.get('allow_ultimate', None)
    )


def run_screen_check(op: Union[ZOperation, ZApplication], screen: MatLike, screenshot_time: float,
                     check_battle_end: bool = True,
                     sync: bool = False) -> None:
    """
    运行画面识别
    :param op: 当前指令
    :param screen: 游戏画面
    :param screenshot_time: 截图时间
    :param check_battle_end: 是否需要识别战斗结束
    :param sync: 是否同步
    :return:
    """
    op.ctx.yolo.check_screen(screen, screenshot_time, sync=sync)
    op.ctx.battle.check_screen(screen, screenshot_time,
                               check_battle_end=check_battle_end,
                               sync=sync)

