import time
from concurrent.futures import Future
from typing import Tuple, Union

from one_dragon.base.operation.operation_round_result import OperationRoundResult
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.game_data.agent import AgentEnum
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
    success, msg = op.auto_op.init_before_running()
    if not success:
        return op.round_fail(msg)

    return op.round_success()

def load_auto_op_async(op: Union[ZOperation, ZApplication], auto_config_sub_dir: str, auto_config_name: str) -> Future[Tuple[bool, str]]:
    if op.auto_op is not None:  # 如果有上一个 先销毁
        op.auto_op.dispose()
    op.auto_op = AutoBattleOperator(op.ctx, auto_config_sub_dir, auto_config_name)
    return op.auto_op.init_before_running_async()


def stop_running(auto_op: AutoBattleOperator) -> None:
    """
    停止自动战斗
    """
    if auto_op is not None:
        auto_op.stop_running()


def resume_running(auto_op: AutoBattleOperator) -> None:
    """
    继续自动战斗
    """
    if auto_op is not None:
        auto_op.start_running_async()


def check_astra_and_switch(auto_op: AutoBattleOperator, timeout_seconds: float = 5) -> None:
    """
    停止后的特殊判断前台是否耀佳音 - 需要切换角色 防止进入状态无法移动
    :return:
    """
    start_time = time.time()
    while True:
        now = time.time()
        if now - start_time >= timeout_seconds:
            break

        screenshot = auto_op.ctx.controller.screenshot()

        auto_op.auto_battle_context.agent_context.check_agent_related(screenshot, now)

        team_info = auto_op.auto_battle_context.agent_context.team_info
        if team_info.agent_list is None or len(team_info.agent_list) == 0:
            time.sleep(0.2)
            continue

        agent = team_info.agent_list[0].agent
        if agent is None:
            time.sleep(0.2)
            continue

        if agent != AgentEnum.ASTRA_YAO.value:  # 不是耀佳音的话 不需要处理
            break

        auto_op.auto_battle_context.switch_next()  # 随便切换下一个角色
        time.sleep(0.2)
