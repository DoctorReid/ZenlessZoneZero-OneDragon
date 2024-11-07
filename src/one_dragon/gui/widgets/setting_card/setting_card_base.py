from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QFrame, QWidget
from dataclasses import dataclass
from qfluentwidgets import SettingCard, FluentIconBase
from qfluentwidgets.components.settings.setting_card import (
    SettingIconWidget,
    FluentStyleSheet,
)
from typing import Union

from one_dragon.gui.utils.layout_utils import Margins, IconSize
from one_dragon.utils.i18_utils import gt


@dataclass
class SettingCardBase(SettingCard):
    title: str
    icon: Union[str, QIcon, FluentIconBase] = None
    iconSize: IconSize = IconSize(16, 16)
    margins: Margins = Margins(16, 16, 0, 16)
    content: str = None
    parent: QWidget = None

    def __post_init__(self):
        """初始化设置卡片，包括布局和组件设置。"""
        # 调用父类的初始化方法
        QFrame.__init__(self, parent=self.parent)

        # 初始化布局
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        # 设置固定高度
        self.setFixedHeight(50)

        # 设置水平布局属性
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(self.margins.left, 0, self.margins.right, 0)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)

        # 设置垂直布局属性
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        # 设置初始参数
        self.titleLabel = QLabel(gt(self.title, "ui"), self)
        self.contentLabel = QLabel(gt(self.content or "", "ui"), self)

        # 处理内容显示
        self.contentLabel.setVisible(bool(self.content))

        # 初始化组件布局

        # 如果有图标，初始化图标组件
        if self.icon is not None:
            self.iconLabel = SettingIconWidget(self.icon, self)
            self.iconLabel.setFixedSize(self.iconSize.width, self.iconSize.height)
            self.hBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignLeft)

        # 添加组件到布局
        self.hBoxLayout.addSpacing(self.margins.top)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(self.margins.bottom)
        self.hBoxLayout.addStretch(1)

        # 设置样式
        self.contentLabel.setObjectName("contentLabel")
        FluentStyleSheet.SETTING_CARD.apply(self)

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self is other

    def setContent(self, content: str):
        """设置卡片内容"""
        self.content = content
        self.contentLabel.setText(gt(content, "ui"))
        self.contentLabel.setVisible(bool(content))  # 根据内容设置可见性

    def setIconSize(self, width: int, height: int):
        """设置图标的固定大小"""
        self.iconSize = IconSize(width, height)
        if hasattr(self, "iconLabel"):  # 确保 iconLabel 已初始化
            self.iconLabel.setFixedSize(width, height)
