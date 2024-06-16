import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentIcon

from one_dragon.envs.project_config import project_config
from one_dragon.gui.view.base_window import BaseFluentWindow
from one_dragon.gui.view.code_interface import CodeInterface
from one_dragon.gui.view.install_interface import InstallerInterface
from one_dragon.utils.i18_utils import gt


class InstallerWindow(BaseFluentWindow):
    """ Main Interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.project_config = project_config
        self.install_interface = InstallerInterface(self)
        self.code_interface = CodeInterface(self)

        self.init_navigation()
        self.init_window()
        self.switchTo(self.code_interface)

    def init_navigation(self):
        self.addSubInterface(self.install_interface, FluentIcon.CLOUD_DOWNLOAD, '安装')
        self.addSubInterface(self.code_interface, FluentIcon.DOCUMENT, '代码')

    def init_window(self):
        title = f"{gt(self.project_config.project_name, 'ui')} {gt('安装器', 'ui')}"
        self.setWindowTitle(title)
        self.resize(960, 720)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = InstallerWindow()
    w.show()
    app.exec()
