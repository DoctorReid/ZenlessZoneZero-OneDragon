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
        FluentWindowBase.__init__(self, ctx=ctx, win_title=win_title, parent=parent)

        self.install_interface = InstallerInterface(ctx, parent=self)
        self.setting_interface = InstallerSettingInterface(ctx, parent=self)

        self.init_navigation()

    def init_navigation(self):
        self.add_sub_interface(self.install_interface)
        self.add_sub_interface(self.setting_interface, position=NavigationItemPosition.BOTTOM)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    _ctx = OneDragonContext()
    setTheme(Theme[_ctx.env_config.theme.upper()])
    w = InstallerWindowBase(_ctx, f'{_ctx.project_config.project_name}-installer')
    w.show()
    app.exec()
