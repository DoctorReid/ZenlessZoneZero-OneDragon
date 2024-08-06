from qfluentwidgets import FluentIcon
from typing import List

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.gui.component.interface.pivot_navi_interface import PivotNavigatorInterface
from one_dragon.gui.component.setting_card.app_run_card import AppRunCard
from one_dragon.gui.view.zzz_one_dragon.one_dragon_run_interface import OneDragonRunInterface
from zzz_od.application.zzz_one_dragon_app import ZOneDragonApp
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.one_dragon.charge_plan_interface import ChargePlanInterface
from zzz_od.gui.view.one_dragon.notorious_hunt_interface import NotoriousHuntPlanInterface


class ZOneDragonInterface(PivotNavigatorInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        PivotNavigatorInterface.__init__(
            self,
            ctx=ctx,
            nav_icon=FluentIcon.BUS,
            object_name='one_dragon_interface',
            parent=parent,
            nav_text_cn='一条龙'
        )

        self._app_run_cards: List[AppRunCard] = []

    def create_sub_interface(self):
        self.add_sub_interface(OneDragonRunInterface(self.ctx, ZOneDragonApp(self.ctx)))
        self.add_sub_interface(ChargePlanInterface(self.ctx))
        self.add_sub_interface(NotoriousHuntPlanInterface(self.ctx))
