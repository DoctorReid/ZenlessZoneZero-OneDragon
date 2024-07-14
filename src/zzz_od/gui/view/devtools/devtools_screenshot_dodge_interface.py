from zzz_od.application.devtools.screenshot_dodge_app import ScreenshotDodgeApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.app_run_interface import AppRunInterface


class DevtoolsScreenshotDodgeInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='devtools_screenshot_dodge_interface',
            nav_text_cn='闪避截图',
            parent=parent
        )

    def get_app(self) -> ZApplication:
        return ScreenshotDodgeApp(self.ctx)
