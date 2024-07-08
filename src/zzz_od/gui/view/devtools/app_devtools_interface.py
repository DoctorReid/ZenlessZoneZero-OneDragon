from qfluentwidgets import qrouter, FluentIcon

from one_dragon.gui.component.interface.pivot_navi_interface import PivotNavigatorInterface
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.devtools.devtools_screenshot_switch_interface import DevtoolsScreenshotSwitchInterface


class AppDevtoolsInterface(PivotNavigatorInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx
        PivotNavigatorInterface.__init__(self, ctx=ctx, object_name='app_devtools_interface', parent=parent,
                                         nav_text_cn='开发工具', nav_icon=FluentIcon.DEVELOPER_TOOLS)

        self.screenshot_switch_interface = DevtoolsScreenshotSwitchInterface(ctx)

        # add items to pivot
        self.add_sub_interface(self.screenshot_switch_interface)
        qrouter.setDefaultRouteKey(self.stacked_widget, self.screenshot_switch_interface.objectName())
