from qfluentwidgets import FluentIcon

from one_dragon.gui.widgets.pivot_navi_interface import PivotNavigatorInterface
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.hollow_zero.hollow_zero_challenge_config_interface import HollowZeroChallengeConfigInterface
from zzz_od.gui.view.hollow_zero.hollow_zero_run_interface import HollowZeroRunInterface
from zzz_od.gui.view.hollow_zero.lost_void_challenge_config_interface import LostVoidChallengeConfigInterface
from zzz_od.gui.view.hollow_zero.lost_void_run_interface import LostVoidRunInterface


class HollowZeroInterface(PivotNavigatorInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx
        PivotNavigatorInterface.__init__(self, object_name='hollow_interface', parent=parent,
                                         nav_text_cn='零号空洞', nav_icon=FluentIcon.IOT)

    def create_sub_interface(self):
        """
        创建下面的子页面
        :return:
        """
        self.add_sub_interface(HollowZeroRunInterface(self.ctx))
        self.add_sub_interface(HollowZeroChallengeConfigInterface(self.ctx))
        self.add_sub_interface(LostVoidRunInterface(self.ctx))
        self.add_sub_interface(LostVoidChallengeConfigInterface(self.ctx))
