import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import NavigationItemPosition, setTheme, Theme

from one_dragon.gui.app.fluent_window_base import FluentWindowBase
from one_dragon.gui.view.code_interface import CodeInterface
from zzz_od.context.zzz_context import ZContext, get_context
from zzz_od.gui.view.devtools.app_devtools_interface import AppDevtoolsInterface
from zzz_od.gui.view.home_interface import HomeInterface
from zzz_od.gui.view.setting.app_setting_interface import AppSettingInterface


class AppWindow(FluentWindowBase):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext
        FluentWindowBase.__init__(
            self,
            ctx=ctx,
            win_title=ctx.project_config.project_name,
            app_icon='app.ico',
            parent=parent
        )

        self.home_interface = HomeInterface(ctx, parent=self)

        self.devtools_interface = AppDevtoolsInterface(ctx, parent=self)
        self.code_interface = CodeInterface(ctx, parent=self)
        self.setting_interface = AppSettingInterface(ctx, parent=self)

        self.init_navigation()

    def init_navigation(self):
        self.add_sub_interface(self.home_interface)

        self.add_sub_interface(self.devtools_interface, position=NavigationItemPosition.BOTTOM)
        self.add_sub_interface(self.code_interface, position=NavigationItemPosition.BOTTOM)
        self.add_sub_interface(self.setting_interface, position=NavigationItemPosition.BOTTOM)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    _ctx = get_context()
    setTheme(Theme[_ctx.env_config.theme.upper()])
    w = AppWindow(_ctx)
    w.show()
    app.exec()
