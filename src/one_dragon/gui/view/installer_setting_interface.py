from qfluentwidgets import FluentIcon

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon.gui.component.interface.pivot_navi_interface import PivotNavigatorInterface
from one_dragon.gui.view.setting.setting_env_interface import SettingEnvInterface


class InstallerSettingInterface(PivotNavigatorInterface):

    def __init__(self, ctx: OneDragonEnvContext, parent=None):
        self.ctx: OneDragonEnvContext = ctx
        PivotNavigatorInterface.__init__(self, object_name='installer_setting_interface', parent=parent,
                                         nav_text_cn='设置', nav_icon=FluentIcon.SETTING)

    def create_sub_interface(self):
        """
        创建下面的子页面
        :return:
        """
        self.add_sub_interface(SettingEnvInterface(self.ctx))
