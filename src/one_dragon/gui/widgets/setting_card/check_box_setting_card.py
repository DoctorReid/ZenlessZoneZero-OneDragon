from PySide6.QtCore import Signal
from PySide6.QtGui import Qt
from dataclasses import dataclass
from qfluentwidgets import SettingCard, CheckBox

from one_dragon.gui.widgets.setting_card.setting_card_base import SettingCardBase
from one_dragon.utils.i18_utils import gt


@dataclass(eq=False)
class CheckBoxSettingCard(SettingCardBase):

    value_changed = Signal(bool)

    def __post_init__(self):
            SettingCardBase.__post_init__(self)
            
            # 初始化 CheckBox
            self.check_box = CheckBox(self)
            self.hBoxLayout.addWidget(self.check_box, 0, Qt.AlignmentFlag.AlignRight)
            self.hBoxLayout.addSpacing(16)

            # 连接信号
            self.check_box.checkStateChanged.connect(self._on_value_changed)

    def _on_value_changed(self, value: Qt.CheckState) -> None:
        """
        值发生改变时 往外发送信号
        :param value:
        :return:
        """
        bool_value = value == Qt.CheckState.Checked
        self.value_changed.emit(bool_value)

    def setContent(self, content: str) -> None:
        """
        更新左侧详细文本
        :param content: 文本 中文
        :return:
        """
        SettingCard.setContent(self, gt(content, "ui"))

    def setValue(self, bool_value: bool) -> None:
        """
        设置值
        :param bool_value:
        :return:
        """
        self.check_box.setChecked(bool_value)
