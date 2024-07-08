from qfluentwidgets import qrouter, FluentIcon

from one_dragon.base.operation.context_base import OneDragonContext
from one_dragon.gui.component.interface.pivot_navi_interface import PivotNavigatorInterface
from one_dragon.gui.view.setting.setting_env_interface import SettingEnvInterface


class AppSettingInterface(PivotNavigatorInterface):

    def __init__(self, ctx: OneDragonContext, parent=None):
        PivotNavigatorInterface.__init__(self, ctx=ctx, object_name='app_setting_interface', parent=parent,
                                         nav_text_cn='设置', nav_icon=FluentIcon.SETTING)

        self.env_interface = SettingEnvInterface(ctx=ctx)

        # add items to pivot
        self.add_sub_interface(self.env_interface)
        qrouter.setDefaultRouteKey(self.stacked_widget, self.env_interface.objectName())

    def init_on_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        self.stacked_widget.currentWidget().init_on_shown()
