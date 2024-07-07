import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import NavigationItemPosition

from one_dragon.envs.project_config import project_config
from one_dragon.gui.component.interface.base_interface import BaseInterface
from one_dragon.gui.view.base_window import BaseFluentWindow
from one_dragon.gui.view.code_interface import CodeInterface
from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext, get_context
from zzz_od.gui.view.devtools.app_devtools_interface import AppDevtoolsInterface
from zzz_od.gui.view.setting.app_setting_interface import AppSettingInterface
from zzz_od.gui.view.home_interface import HomeInterface


class InstallerWindow(BaseFluentWindow):
    """ Main Interface """

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        BaseFluentWindow.__init__(self, parent=parent)

        self.project_config = project_config
        self.home_interface = HomeInterface(self)

        self.devtools_interface = AppDevtoolsInterface(self.ctx, parent=self)
        self.code_interface = CodeInterface(parent=self)
        self.setting_interface = AppSettingInterface(parent=self)

        self.init_navigation()
        self.init_window()

    def init_navigation(self):
        self.add_sub_interface(self.home_interface)

        self.add_sub_interface(self.devtools_interface, position=NavigationItemPosition.BOTTOM)
        self.add_sub_interface(self.code_interface, position=NavigationItemPosition.BOTTOM)
        self.add_sub_interface(self.setting_interface, position=NavigationItemPosition.BOTTOM)

    def add_sub_interface(self, interface: BaseInterface, position=NavigationItemPosition.TOP):
        self.addSubInterface(interface, interface.nav_icon, interface.nav_text, position=position)

    def init_window(self):
        title = f"{gt(self.project_config.project_name, 'ui')}"
        self.setWindowTitle(title)
        app_icon_path = os.path.join(os_utils.get_path_under_work_dir('assets', 'ui'), 'app.ico')
        self.setWindowIcon(QIcon(app_icon_path))
        self.resize(960, 820)
        self.move(100, 100)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = InstallerWindow(get_context())
    w.show()
    app.exec()
