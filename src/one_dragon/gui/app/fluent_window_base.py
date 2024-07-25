import os
from PySide6.QtCore import QSize
from typing import Optional

from PySide6.QtGui import QIcon
from qfluentwidgets import FluentWindow, NavigationItemPosition, SplashScreen

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.gui.component.interface.base_interface import BaseInterface
from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt


class FluentWindowBase(FluentWindow):

    def __init__(self,
                 ctx: OneDragonContext,
                 win_title: str,
                 app_icon: Optional[str] = None,
                 parent=None):
        super().__init__(parent=parent)
        self.ctx: OneDragonContext = ctx
        self._last_stack_idx: int = 0

        self.init_window(win_title, app_icon)

        # 1. 创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(144, 144))

        # 2. 在创建其他子页面前先显示主界面
        self.show()

        self.stackedWidget.currentChanged.connect(self.init_interface_on_shown)
        self.create_sub_interface()

        # 4. 隐藏启动页面
        self.splashScreen.finish()

    def create_sub_interface(self) -> None:
        """
        创建子页面
        :return:
        """
        pass

    def add_sub_interface(self, interface: BaseInterface, position=NavigationItemPosition.TOP):
        self.addSubInterface(interface, interface.nav_icon, interface.nav_text, position=position)

    def init_window(self,
                    win_title: str,
                    app_icon: Optional[str] = None):
        self.setWindowTitle(gt(win_title, 'ui'))
        if app_icon is not None:
            app_icon_path = os.path.join(os_utils.get_path_under_work_dir('assets', 'ui'), app_icon)
            self.setWindowIcon(QIcon(app_icon_path))
        self.resize(960, 820)
        self.move(100, 100)

    def init_interface_on_shown(self, index: int) -> None:
        """
        切换子界面时 初始化子界面的显示
        :return:
        """
        if index != self._last_stack_idx:
            last_interface: BaseInterface = self.stackedWidget.widget(self._last_stack_idx)
            if isinstance(last_interface, BaseInterface):
                last_interface.on_interface_hidden()
            self._last_stack_idx = index

        base_interface: BaseInterface = self.stackedWidget.currentWidget()
        if isinstance(base_interface, BaseInterface):
            base_interface.on_interface_shown()
