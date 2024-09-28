from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, Qt
from qfluentwidgets import SettingCard, FluentIconBase, LineEdit
from typing import Union, Optional

from one_dragon.gui.component.setting_card.setting_card_base import SettingCardBase
from one_dragon.gui.component.setting_card.yaml_config_adapter import YamlConfigAdapter
from one_dragon.utils.i18_utils import gt


class TextSettingCard(SettingCardBase):

    value_changed = Signal(str)

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title: str, content=None, parent=None,
                 input_placeholder: str = None, input_max_width: int = 300,
                 adapter: Optional[YamlConfigAdapter] = None):
        """
        :param icon: 左边显示的图标
        :param title: 左边的标题 中文
        :param content: 左侧的详细文本 中文
        :param parent: 组件的parent
        :param input_placeholder: 输入提示
        :param input_max_width: 输入框的最大长度
        :param adapter: 配置适配器 自动更新对应配置文件
        """
        SettingCardBase.__init__(self, icon, title, content, parent)
        self.adapter: YamlConfigAdapter = adapter

        self.line_edit = LineEdit(self)
        self.line_edit.setMaximumWidth(input_max_width)
        self.line_edit.setPlaceholderText(input_placeholder)
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.editingFinished.connect(self._on_text_changed)

        self.hBoxLayout.addWidget(self.line_edit, 1, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _on_text_changed(self) -> None:
        val = self.line_edit.text()
        self.value_changed.emit(val)

        if self.adapter is not None:
            self.adapter.set_value(val)

    def init_with_adapter(self, adapter: YamlConfigAdapter) -> None:
        """
        初始化值
        """
        self.adapter = adapter
        self.setValue(self.adapter.get_value(), emit_signal=False)

    def setContent(self, content: str) -> None:
        """
        更新左侧详细文本
        :param content: 文本 中文
        :return:
        """
        SettingCard.setContent(self, gt(content, 'ui'))

    def setValue(self, value: str, emit_signal: bool = True) -> None:
        """
        设置值
        :param value:
        :param emit_signal: 是否发送信号
        :return:
        """
        if not emit_signal:
            self.line_edit.blockSignals(True)
        self.line_edit.setText(value)
        if not emit_signal:
            self.line_edit.blockSignals(False)
