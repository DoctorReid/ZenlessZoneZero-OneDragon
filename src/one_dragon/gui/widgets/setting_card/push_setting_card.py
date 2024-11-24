from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton
from dataclasses import dataclass

from one_dragon.gui.widgets.setting_card.setting_card_base import SettingCardBase


@dataclass(eq=False)
class PushSettingCard(SettingCardBase):
    """带推送按钮的设置卡片类"""

    title: str
    value: str = ""

    # 定义信号
    clicked = Signal()
    text: str = ''

    def __post_init__(self):
        # 初始化父类的属性和布局
        SettingCardBase.__post_init__(self)

        # 创建按钮并添加到布局中
        self.button = QPushButton(self.text, self)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        # 连接按钮点击信号到自定义的 clicked 信号
        self.button.clicked.connect(self.clicked.emit)
