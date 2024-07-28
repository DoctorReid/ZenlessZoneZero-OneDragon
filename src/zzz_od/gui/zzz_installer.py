import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import NavigationItemPosition, Theme, setTheme

from one_dragon.gui.app.fluent_window_base import FluentWindowBase
from one_dragon.gui.view.install_interface import InstallerInterface
from one_dragon.gui.view.installer_setting_interface import InstallerSettingInterface
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.installer.extend_install_interface import ExtendInstallInterface


class ZInstallerWindow(FluentWindowBase):

    def __init__(self, ctx: ZContext, win_title: str, parent=None):
        self.ctx: ZContext = ctx
        FluentWindowBase.__init__(
            self,
            ctx=ctx,
            win_title=win_title,
            parent=parent,
            app_icon='zzz_logo.ico'
        )

    def create_sub_interface(self):
        self.add_sub_interface(InstallerInterface(self.ctx, parent=self))
        self.add_sub_interface(ExtendInstallInterface(self.ctx, parent=self))
        self.add_sub_interface(InstallerSettingInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    _ctx = ZContext()
    setTheme(Theme[_ctx.env_config.theme.upper()])
    w = ZInstallerWindow(_ctx, f'{_ctx.project_config.project_name}-installer')
    w.show()
    app.exec()
