from qfluentwidgets import FluentIcon

from zzz_od.application.devtools.screenshot_switch_app import ScreenshotSwitchApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.app_run_interface import AppRunInterface


class SwitchAssistantInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='switch_assistant,interface',
            nav_text_cn='闪避助手',
            nav_icon=FluentIcon.PLAY,
            parent=parent
        )

    def get_app(self) -> ZApplication:
        return ScreenshotSwitchApp(self.ctx)
