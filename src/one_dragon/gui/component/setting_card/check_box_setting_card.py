from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, Qt
from qfluentwidgets import SettingCard, FluentIconBase, CheckBox
from typing import Union

from one_dragon.gui.component.setting_card.setting_card_base import SettingCardBase
from one_dragon.utils.i18_utils import gt


class CheckBoxSettingCard(SettingCardBase):

    value_changed = Signal(bool)

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title: str, content=None, parent=None):
        """
        :param icon: 左边显示的图标
        :param title: 左边的标题 中文
        :param content: 左侧的详细文本 中文
        :param parent: 组件的parent
        """
        SettingCardBase.__init__(self, icon, title, content, parent)
        self.check_box = CheckBox(self)
        self.hBoxLayout.addWidget(self.check_box, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

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
        SettingCard.setContent(self, gt(content, 'ui'))

    def setValue(self, bool_value: bool) -> None:
        """
        设置值
        :param bool_value:
        :return:
        """
        self.check_box.setChecked(bool_value)
