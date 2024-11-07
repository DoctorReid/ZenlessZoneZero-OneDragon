from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractButton, QVBoxLayout, QHBoxLayout
from dataclasses import dataclass, field
from typing import List

from one_dragon.gui.widgets.setting_card.setting_card_base import SettingCardBase


@dataclass(eq=False)
class MultiPushSettingCard(SettingCardBase):
    """带多个按钮的设置卡片类"""

    title: str
    btn_list: List[QAbstractButton] = field(default_factory=list)
    
    def __post_init__(self):
        SettingCardBase.__post_init__(self)
        
        # 初始化按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.addStretch(1)
        for btn in self.btn_list:
            btn_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
        btn_layout.addSpacing(16)

        # 将按钮布局添加到卡片的主布局中
        self.hBoxLayout.addLayout(btn_layout, 1)


@dataclass(eq=False)
class MultiLineSettingCard(SettingCardBase):
    """带多行按钮的设置卡片类"""

    title: str
    line_list: List[List[QAbstractButton]] = field(default_factory=list)

    def __post_init__(self):
        SettingCardBase.__post_init__(self)

        # 初始化纵向布局
        v_layout = QVBoxLayout()
        v_layout.setSpacing(5)
        self.hBoxLayout.addLayout(v_layout)

        # 创建每一行的按钮布局
        for line in self.line_list:
            h_layout = QHBoxLayout()
            h_layout.setSpacing(16)
            v_layout.addLayout(h_layout)
            h_layout.addStretch(1)
            for btn in line:
                h_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)

        # 根据按钮行数调整卡片的高度
        self.setFixedHeight(50 + (len(self.line_list) - 1) * 30)
