from qfluentwidgets import FluentWindow

from one_dragon.gui.view.base_interface import BaseInterface


class BaseFluentWindow(FluentWindow):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.stackedWidget.currentChanged.connect(self.init_interface_on_shown)

    def init_interface_on_shown(self) -> None:
        """
        切换子界面时 初始化子界面的显示
        :return:
        """
        interface = self.stackedWidget.currentWidget()
        if isinstance(interface, BaseInterface):
            base_interface: BaseInterface = interface
            base_interface.init_on_shown()
