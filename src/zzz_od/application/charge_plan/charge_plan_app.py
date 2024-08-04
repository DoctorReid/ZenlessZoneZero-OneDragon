from typing import ClassVar, Optional

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.config.charge_plan_config import ChargePlanItem
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.compendium.combat_simulation import CombatSimulation
from zzz_od.operation.compendium.tp_by_compendium import TransportByCompendium


class ChargePlanApp(ZApplication):

    STATUS_NO_PLAN: ClassVar[str] = '未配置电量计划'

    def __init__(self, ctx: ZContext):
        """
        每天自动接收邮件奖励
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='charge_plan',
            node_max_retry_times=10,
            op_name=gt('电量刷本', 'ui'),
            run_record=ctx.charge_plan_run_record
        )

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        self.next_plan: Optional[ChargePlanItem] = None

    @node_from(from_name='实战模拟室')
    @node_from(from_name='定期清剿')
    @node_from(from_name='专业挑战室')
    @operation_node(name='传送', is_start_node=True)
    def transport(self) -> OperationRoundResult:
        next_plan = self.ctx.charge_plan_config.get_next_plan()
        if next_plan is None:
            return self.round_fail(ChargePlanApp.STATUS_NO_PLAN)

        self.next_plan = next_plan
        op = TransportByCompendium(self.ctx,
                                   next_plan.tab_name,
                                   next_plan.category_name,
                                   next_plan.mission_type_name)
        return self.round_by_op(op.execute())

    @node_from(from_name='传送')
    @operation_node(name='识别副本分类')
    def check_mission_type(self) -> OperationRoundResult:
        return self.round_success(self.next_plan.category_name)

    @node_from(from_name='识别副本分类', status='实战模拟室')
    @operation_node(name='实战模拟室')
    def combat_simulation(self) -> OperationRoundResult:
        op = CombatSimulation(self.ctx, self.next_plan)
        return self.round_by_op(op.execute())

    @node_from(from_name='识别副本分类', status='定期清剿')
    @operation_node(name='定期清剿')
    def routine_cleanup(self) -> OperationRoundResult:
        return self.round_fail('未支持')

    @node_from(from_name='识别副本分类', status='专业挑战室')
    @operation_node(name='专业挑战室')
    def expert_challenge(self) -> OperationRoundResult:
        return self.round_fail('未支持')
