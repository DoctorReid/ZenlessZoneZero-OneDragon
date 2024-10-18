from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import  QHBoxLayout, QLabel, QVBoxLayout,QFrame
from qfluentwidgets import SettingCard, FluentIconBase
from qfluentwidgets.components.settings.setting_card import SettingIconWidget,FluentStyleSheet
from typing import Union

from one_dragon.gui.component.layout_utils import Margins, IconSize
from one_dragon.utils.i18_utils import gt

class SettingCardBase(SettingCard):

    def __init__(self, title:str,
                icon: Union[str, QIcon, FluentIconBase]=None,
                iconSize:IconSize = IconSize(16,16),
                margins:Margins = Margins(16,16,0,16),
                content=None, parent=None):
        """
        稍微改造原库里的SettingCard
        """
        
        QFrame.__init__(self, parent=parent)  # 不初始化SettingCard 初始化其父类
            
        title=gt(title, 'ui')

        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(content or '', self)
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        # SettingCard初始化的时候有无content的高度不一致 因此统一不使用构造器传入
        if not content:
            self.contentLabel.hide()

        if content is not None:
            self.setContent(gt(content, 'ui'))

        self.setFixedHeight(70 if content else 50)
        

        # initialize layout
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(margins.left, 0, margins.right, 0)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        if icon is not None:
            self.iconLabel = SettingIconWidget(icon, self)
            self.iconLabel.setFixedSize(iconSize.width, iconSize.height)
            self.hBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignLeft)

        self.hBoxLayout.addSpacing(margins.top)

        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignLeft)

        self.hBoxLayout.addSpacing(margins.bottom)
        self.hBoxLayout.addStretch(1)

        self.contentLabel.setObjectName('contentLabel')
        FluentStyleSheet.SETTING_CARD.apply(self)