from qfluentwidgets import FluentIcon

from one_dragon.gui.component.interface.pivot_navi_interface import PivotNavigatorInterface
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.battle_assistant.auto_battle_interface import AutoBattleInterface
from zzz_od.gui.view.battle_assistant.dodge_assistant_interface import DodgeAssistantInterface
from zzz_od.gui.view.battle_assistant.operation_debug_interface import OperationDebugInterface


class BattleAssistantInterface(PivotNavigatorInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx
        PivotNavigatorInterface.__init__(self, ctx=ctx, object_name='battle_assistant_interface', parent=parent,
                                         nav_text_cn='战斗助手', nav_icon=FluentIcon.GAME)

    def create_sub_interface(self):
        """
        创建下面的子页面
        :return:
        """
        self.add_sub_interface(DodgeAssistantInterface(self.ctx))
        self.add_sub_interface(AutoBattleInterface(self.ctx))
        self.add_sub_interface(OperationDebugInterface(self.ctx))
