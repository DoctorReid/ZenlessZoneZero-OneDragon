import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import NavigationItemPosition, Theme, setTheme

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.gui.app.fluent_window_base import FluentWindowBase
from one_dragon.gui.common.od_style_sheet import OdStyleSheet
from one_dragon.gui.view.install_interface import InstallerInterface
from one_dragon.gui.view.installer_setting_interface import InstallerSettingInterface
from one_dragon.utils.i18_utils import gt


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

    
    # 继承初始化函数
    def init_window(self):
        self.resize(960, 640)

        # 初始化位置
        self.move(100, 100)

        # 设置配置ID
        self.setObjectName("OneDragonWindow")
        self.navigationInterface.setObjectName("NavigationInterface")
        self.stackedWidget.setObjectName("StackedWidget")
        self.titleBar.setObjectName("TitleBar")    

        # 布局样式调整
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.stackedWidget.setContentsMargins(0, 28, 0, 0)
        self.navigationInterface.setContentsMargins(0, 28, 0, 0)

        # 配置样式
        OdStyleSheet.APP_WINDOW.apply(self)
        OdStyleSheet.NAVIGATION_INTERFACE.apply(self.navigationInterface)
        OdStyleSheet.STACKED_WIDGET.apply(self.stackedWidget)
        OdStyleSheet.TITLE_BAR.apply(self.titleBar)

    def create_sub_interface(self):
        self.add_sub_interface(InstallerInterface(self.ctx, parent=self))
        self.add_sub_interface(InstallerSettingInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    _ctx = OneDragonContext()
    setTheme(Theme[_ctx.env_config.theme.upper()])
    w = InstallerWindowBase(_ctx, gt(f'{_ctx.project_config.project_name}-installer', 'ui'))
    w.show()
    app.exec()
