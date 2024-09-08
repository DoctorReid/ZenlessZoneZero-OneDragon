from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIconBase
from typing import Union

from one_dragon.utils.i18_utils import gt


class BaseInterface(QWidget):

    def __init__(self,
                 object_name: str,
                 nav_text_cn: str,
                 nav_icon: Union[FluentIconBase, QIcon, str] = None,
                 parent=None):
        """
        包装一个子页面需要有的内容
        :param object_name: 导航用的唯一键
        :param nav_text_cn: 出现在导航上的中文
        :param nav_icon: 出现在导航上的图标
        """
        QWidget.__init__(self, parent=parent)
        self.nav_text: str = gt(nav_text_cn, 'ui')
        self.nav_icon: Union[FluentIconBase, QIcon, str] = nav_icon
        self.setObjectName(object_name)

    def on_interface_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        pass

    def on_interface_hidden(self) -> None:
        """
        子界面隐藏时的回调
        :return:
        """
        pass