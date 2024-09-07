from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QAbstractButton, QWidget
from qfluentwidgets import FluentIconBase
from typing import Union, List, Optional

from one_dragon.gui.component.setting_card.setting_card_base import SettingCardBase


class MultiPushSettingCard(SettingCardBase):

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
        SettingCardBase.__init__(self, icon, title, content, parent)

        for i in range(len(btn_list)):
            self.hBoxLayout.addWidget(btn_list[i], alignment=Qt.AlignmentFlag.AlignRight)
            self.hBoxLayout.addSpacing(16)
