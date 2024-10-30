from PySide6.QtCore import Signal, Qt
from dataclasses import dataclass
from qfluentwidgets import LineEdit
from typing import Optional

from one_dragon.gui.component.setting_card.setting_card_base import SettingCardBase
from one_dragon.gui.component.setting_card.yaml_config_adapter import YamlConfigAdapter
from one_dragon.utils.i18_utils import gt


@dataclass(eq=False)
class TextSettingCard(SettingCardBase):
    """带文本输入框的设置卡片类"""

    title: str
    input_placeholder: Optional[str] = None
    input_max_width: int = 300
    adapter: Optional[YamlConfigAdapter] = None

    value_changed = Signal(str)

    def __post_init__(self):
        # 初始化父类
        SettingCardBase.__post_init__(self)

        # 创建 LineEdit 控件并设置相关属性
        self.line_edit = LineEdit(self)
        self.line_edit.setMaximumWidth(self.input_max_width)
        self.line_edit.setPlaceholderText(self.input_placeholder)
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.editingFinished.connect(self._on_text_changed)

        # 将输入框添加到布局
        self.hBoxLayout.addWidget(self.line_edit, 1, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _on_text_changed(self) -> None:
        """处理文本更改事件"""
        val = self.line_edit.text()
        self.value_changed.emit(val)

        if self.adapter is not None:
            self.adapter.set_value(val)

    def init_with_adapter(self, adapter: Optional[YamlConfigAdapter]) -> None:
        """使用配置适配器初始化值"""
        self.adapter = adapter

        if self.adapter is None:
            self.setValue("", emit_signal=False)
        else:
            self.setValue(self.adapter.get_value(), emit_signal=False)

    def setContent(self, content: str) -> None:
        """更新左侧详细文本"""
        SettingCardBase.setContent(self, gt(content, "ui"))

    def setValue(self, value: str, emit_signal: bool = True) -> None:
        """设置输入框的值"""
        if not emit_signal:
            self.line_edit.blockSignals(True)
        self.line_edit.setText(value)
        if not emit_signal:
            self.line_edit.blockSignals(False)
