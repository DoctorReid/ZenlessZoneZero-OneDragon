from typing import Union

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, Qt
from qfluentwidgets import SettingCard, FluentIconBase, LineEdit

from one_dragon.utils.i18_utils import gt


class TextSettingCard(SettingCard):

    value_changed = Signal(str)

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title: str, content=None, parent=None,
                 input_placeholder: str = None, input_max_width: int = 300):
        """
        :param icon: 左边显示的图标
        :param title: 左边的标题 中文
        :param content: 左侧的详细文本 中文
        :param parent: 组件的parent
        :param input_placeholder: 输入提示
        :param input_max_width: 输入框的最大长度
        """
        SettingCard.__init__(self, icon, gt(title, 'ui'), gt(content, 'ui'), parent)
        self.line_edit = LineEdit(self)
        self.line_edit.setMaximumWidth(input_max_width)
        self.line_edit.setPlaceholderText(input_placeholder)
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.editingFinished.connect(self._on_text_changed)

        self.hBoxLayout.addWidget(self.line_edit, 1, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _on_text_changed(self) -> None:
        self.value_changed.emit(self.line_edit.text())

    def setContent(self, content: str) -> None:
        """
        更新左侧详细文本
        :param content: 文本 中文
        :return:
        """
        SettingCard.setContent(self, gt(content, 'ui'))

    def setValue(self, value: str) -> None:
        """
        设置值
        :param value:
        :return:
        """
        self.line_edit.setText(value)
