import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import NavigationItemPosition, setTheme, Theme

from one_dragon.gui.app.fluent_window_base import FluentWindowBase
from one_dragon.gui.view.code_interface import CodeInterface
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.battle_assistant.battle_assistant_interface import BattleAssistantInterface
from zzz_od.gui.view.devtools.app_devtools_interface import AppDevtoolsInterface
from zzz_od.gui.view.home_interface import HomeInterface
from zzz_od.gui.view.one_dragon.zzz_one_dragon_interface import ZOneDragonInterface
from zzz_od.gui.view.setting.app_setting_interface import AppSettingInterface


class AppWindow(FluentWindowBase):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        FluentWindowBase.__init__(
            self,
            ctx=ctx,
            win_title=ctx.project_config.project_name,
            app_icon='zzz_logo.ico',
            parent=parent
        )

    def create_sub_interface(self):
        self.add_sub_interface(HomeInterface(self.ctx, parent=self))
        self.add_sub_interface(BattleAssistantInterface(self.ctx, parent=self))
        self.add_sub_interface(ZOneDragonInterface(self.ctx, parent=self))

        self.add_sub_interface(AppDevtoolsInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)
        self.add_sub_interface(CodeInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)
        self.add_sub_interface(AppSettingInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    _ctx = ZContext()
    _ctx.init_by_config()
    setTheme(Theme[_ctx.env_config.theme.upper()])
    w = AppWindow(_ctx)
    w.show()
    w.activateWindow()
    app.exec()
