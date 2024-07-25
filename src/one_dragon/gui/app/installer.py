import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import NavigationItemPosition, Theme, setTheme

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.gui.app.fluent_window_base import FluentWindowBase
from one_dragon.gui.view.install_interface import InstallerInterface
from one_dragon.gui.view.installer_setting_interface import InstallerSettingInterface


class InstallerWindowBase(FluentWindowBase):
    """ Main Interface """

    def __init__(self, ctx: OneDragonContext, win_title: str, parent=None):
        FluentWindowBase.__init__(
            self,
            ctx=ctx,
            win_title=win_title,
            parent=parent,
            app_icon='zzz_logo.ico'
        )

    def create_sub_interface(self):
        self.add_sub_interface(InstallerInterface(self.ctx, parent=self))
        self.add_sub_interface(InstallerSettingInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    _ctx = OneDragonContext()
    setTheme(Theme[_ctx.env_config.theme.upper()])
    w = InstallerWindowBase(_ctx, f'{_ctx.project_config.project_name}-installer')
    w.show()
    app.exec()
