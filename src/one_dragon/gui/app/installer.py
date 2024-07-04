import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentIcon, NavigationItemPosition

from one_dragon.envs.project_config import project_config
from one_dragon.gui.view.base_window import BaseFluentWindow
from one_dragon.gui.view.code_interface import CodeInterface
from one_dragon.gui.view.install_interface import InstallerInterface
from one_dragon.gui.view.installer_setting_interface import InstallerSettingInterface
from one_dragon.utils.i18_utils import gt


class InstallerWindow(BaseFluentWindow):
    """ Main Interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.project_config = project_config
        self.install_interface = InstallerInterface(self)
        self.code_interface = CodeInterface(self)
        self.setting_interface = InstallerSettingInterface(self)

        self.init_navigation()
        self.init_window()

    def init_navigation(self):
        self.addSubInterface(self.install_interface, self.install_interface.nav_icon, self.install_interface.nav_text)
        self.addSubInterface(self.code_interface, self.code_interface.nav_icon, self.code_interface.nav_text)
        self.addSubInterface(self.setting_interface, self.setting_interface.nav_icon, self.setting_interface.nav_text, position=NavigationItemPosition.BOTTOM)

    def init_window(self):
        title = f"{gt(self.project_config.project_name, 'ui')} {gt('安装器', 'ui')}"
        self.setWindowTitle(title)
        self.resize(960, 820)
        self.move(100, 100)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = InstallerWindow()
    w.show()
    app.exec()
