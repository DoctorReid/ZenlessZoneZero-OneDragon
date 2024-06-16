from typing import Union, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QAbstractButton, QWidget
from qfluentwidgets import SettingCard, FluentIconBase


class MultiPushSettingCard(SettingCard):

    def __init__(self, btn_list: List[QAbstractButton], icon: Union[str, QIcon, FluentIconBase],
                 title: str, content: Optional[str] = None, parent: Optional[QWidget] = None):
        """
        Parameters
        ----------
        btn_list: str
            the list of push button

        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        parent: QWidget
            parent widget
        """
        super().__init__(icon, title, content, parent)

        for i in range(len(btn_list)):
            self.hBoxLayout.addWidget(btn_list[i], alignment=Qt.AlignmentFlag.AlignRight)
            self.hBoxLayout.addSpacing(16)
