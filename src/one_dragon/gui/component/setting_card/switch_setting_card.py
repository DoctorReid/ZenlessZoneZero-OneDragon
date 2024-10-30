from PySide6.QtCore import Signal, Qt
from dataclasses import dataclass
from qfluentwidgets import SwitchButton, IndicatorPosition
from typing import Optional

from one_dragon.gui.component.setting_card.setting_card_base import SettingCardBase
from one_dragon.gui.component.setting_card.yaml_config_adapter import YamlConfigAdapter
from one_dragon.utils.i18_utils import gt


@dataclass(eq=False)
class SwitchSettingCard(SettingCardBase):
    """带切换开关的设置卡片类"""

    title: str
    on_text_cn: str = "开"
    off_text_cn: str = "关"
    adapter: Optional[YamlConfigAdapter] = None

    value_changed = Signal(bool)

    def __post_init__(self):
        # 初始化父类
        SettingCardBase.__post_init__(self)

        # 创建按钮并设置相关属性
        self.btn = SwitchButton(parent=self, indicatorPos=IndicatorPosition.RIGHT)
        self.btn._offText = gt(self.off_text_cn, "ui")
        self.btn._onText = gt(self.on_text_cn, "ui")
        self.btn.checkedChanged.connect(self._on_value_changed)

        # 将按钮添加到布局
        self.hBoxLayout.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _on_value_changed(self, value: bool):
        # 更新配置适配器中的值并发出信号
        if self.adapter is not None:
            self.adapter.set_value(value)
        self.value_changed.emit(value)

    def init_with_adapter(self, adapter: YamlConfigAdapter) -> None:
        """使用配置适配器初始化值"""
        self.adapter = adapter
        self.setValue(self.adapter.get_value(), emit_signal=False)

    def setValue(self, value: bool, emit_signal: bool = True):
        """设置开关状态并更新文本"""
        if not emit_signal:
            self.btn.blockSignals(True)
        self.btn.setChecked(value)
        text = self.on_text_cn if value else self.off_text_cn
        self.btn.setText(gt(text, "ui"))
        if not emit_signal:
            self.btn.blockSignals(False)
