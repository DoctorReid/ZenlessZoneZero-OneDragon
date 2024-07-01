import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentIcon

from one_dragon.envs.project_config import project_config
from one_dragon.gui.view.base_window import BaseFluentWindow
from one_dragon.gui.view.code_interface import CodeInterface
from one_dragon.gui.view.install_interface import InstallerInterface
from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.gui.view.home_interface import HomeInterface


class InstallerWindow(BaseFluentWindow):
    """ Main Interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.project_config = project_config
        self.home_interface = HomeInterface(self)

        self.init_navigation()
        self.init_window()

    def init_navigation(self):
        self.addSubInterface(self.home_interface, FluentIcon.CLOUD_DOWNLOAD, '主页')

    def init_window(self):
        title = f"{gt(self.project_config.project_name, 'ui')}"
        self.setWindowTitle(title)
        app_icon_path = os.path.join(os_utils.get_path_under_work_dir('assets', 'ui'), 'app.ico')
        self.setWindowIcon(QIcon(app_icon_path))
        self.resize(960, 820)
        self.move(100, 100)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = InstallerWindow()
    w.show()
    app.exec()
