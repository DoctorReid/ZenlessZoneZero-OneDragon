from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QAbstractButton, QWidget, QVBoxLayout, QHBoxLayout
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

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.addStretch(1)
        for i in range(len(btn_list)):
            btn_layout.addWidget(btn_list[i], alignment=Qt.AlignmentFlag.AlignRight)
        btn_layout.addSpacing(16)

        self.hBoxLayout.addLayout(btn_layout, 1)


class MultiLineSettingCard(SettingCardBase):

    def __init__(self, line_list: List[List[QAbstractButton]], icon: Union[str, QIcon, FluentIconBase],
                 title: str, content: Optional[str] = None, parent: Optional[QWidget] = None):
        SettingCardBase.__init__(self, icon, title, content, parent)

        v_layout = QVBoxLayout()
        v_layout.setSpacing(5)
        self.hBoxLayout.addLayout(v_layout)

        for line in line_list:
            h_layout = QHBoxLayout()
            h_layout.setSpacing(16)
            v_layout.addLayout(h_layout)
            h_layout.addStretch(1)
            for btn in line:
                h_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.setFixedHeight(50 + (len(line_list) - 1) * 30)
