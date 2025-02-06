from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QFrame
from qfluentwidgets import SettingCard, FluentIconBase
from qfluentwidgets.components.settings.setting_card import (
    SettingIconWidget,
    FluentStyleSheet,
)
from typing import Union

from one_dragon.utils.i18_utils import gt
from one_dragon_qt.utils.layout_utils import Margins, IconSize


class SettingCardBase(SettingCard):

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None,
                 icon_size: IconSize = IconSize(16, 16),
                 margins: Margins = Margins(16, 16, 0, 16),
                 parent=None):
        QFrame.__init__(self, parent=parent)

        # 初始化布局
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        # 设置固定高度
        self.setFixedHeight(50)

        # 设置水平布局属性
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(margins.left, 0, margins.right, 0)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # 设置垂直布局属性
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # 设置初始参数
        self.titleLabel = QLabel(gt(title, "ui"), self)
        self.contentLabel = QLabel(gt(content, "ui"), self)

        # 处理内容显示
        self.contentLabel.setVisible(bool(content))

        # 如果有图标，初始化图标组件
        if icon is not None:
            self.iconLabel = SettingIconWidget(icon, self)
            self.iconLabel.setFixedSize(icon_size.width, icon_size.height)
            self.hBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignmentFlag.AlignLeft)

        # 添加组件到布局
        self.hBoxLayout.addSpacing(margins.top)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.hBoxLayout.addSpacing(margins.bottom)
        self.hBoxLayout.addStretch(1)

        # 设置样式
        self.contentLabel.setObjectName("contentLabel")
        FluentStyleSheet.SETTING_CARD.apply(self)

    def setContent(self, content: str):
        """设置卡片内容"""
        self.contentLabel.setText(gt(content, "ui"))
        self.contentLabel.setVisible(content is not None and len(content) > 0)  # 根据内容设置可见性

    def setIconSize(self, width: int, height: int):
        """设置图标的固定大小"""
        if hasattr(self, "iconLabel"):  # 确保 iconLabel 已初始化
            self.iconLabel.setFixedSize(width, height)
