from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QPushButton
from qfluentwidgets import FluentIconBase
from one_dragon.gui.component.layout_utils import IconSize, Margins
from one_dragon.gui.component.setting_card.setting_card_base import SettingCardBase
from typing import Union

class PushSettingCard(SettingCardBase):
    """ Setting card with a push button """

    clicked = Signal()

    def __init__(self,text:str,title:str,icon: Union[str, QIcon, FluentIconBase]=None,
                iconSize:IconSize = IconSize(16,16),
                margins:Margins = Margins(16,16,0,16), value: str = '', content=None, parent=None):
        """
        Parameters
        ----------
        text: str
            the text of push button

        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        parent: QWidget
            parent widget
        """
        super().__init__(title,icon,iconSize,margins, content, parent)
        self.button = QPushButton(text, self)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.button.clicked.connect(self.clicked)