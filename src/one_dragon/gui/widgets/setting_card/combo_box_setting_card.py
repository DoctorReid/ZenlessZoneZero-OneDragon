from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtGui import QColor
from dataclasses import dataclass, field
from enum import Enum
from qfluentwidgets import ToolTip
from typing import Optional, List, Iterable

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.gui.widgets.setting_card.setting_card_base import SettingCardBase
from one_dragon.gui.widgets.setting_card.yaml_config_adapter import YamlConfigAdapter

from phosdeiz.gui.widgets import ComboBox


@dataclass(eq=False)
class ComboBoxSettingCard(SettingCardBase):
    """包含下拉框的自定义设置卡片类。"""

    title: str
    options_enum: Optional[Iterable[Enum]] = None
    options_list: Optional[List[ConfigItem]] = field(default_factory=list)
    tooltip: Optional[str] = None
    adapter: Optional[YamlConfigAdapter] = None
    
    value_changed = Signal(int, object)

    def __post_init__(self):
        """初始化设置卡片，设置下拉框及其选项。"""
        SettingCardBase.__post_init__(self)

        # 初始化下拉框
        self.combo_box = ComboBox(self)
        self.hBoxLayout.addWidget(self.combo_box, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        # 处理工具提示
        self._tooltip: Optional[ToolTip] = None
        if self.tooltip:
            self.titleLabel.installEventFilter(self)

        # 初始化选项
        self._opts_list: List[ConfigItem] = []
        self._initialize_options(self.options_enum, self.options_list)

        # 设置初始索引
        self.last_index = -1
        if self.combo_box.count() > 0:
            self.combo_box.setCurrentIndex(0)
            self.last_index = 0

        # 连接信号与槽
        self.combo_box.currentIndexChanged.connect(self._on_index_changed)

    def _initialize_options(self, options_enum: Optional[Iterable[Enum]], options_list: Optional[List[ConfigItem]]) -> None:
        """从枚举或列表初始化下拉框选项。"""
        if options_enum:
            for opt in options_enum:
                if isinstance(opt.value, ConfigItem):
                    self._opts_list.append(opt.value)
                    self.combo_box.addItem(opt.value.ui_text, userData=opt.value.value)
        elif options_list:
            for opt_item in options_list:
                self._opts_list.append(opt_item)
                self.combo_box.addItem(opt_item.ui_text, userData=opt_item.value)

    def eventFilter(self, obj, event: QEvent) -> bool:
        """处理标题标签的鼠标事件。"""
        if obj == self.titleLabel:
            if event.type() == QEvent.Type.Enter:
                self._show_tooltip()
            elif event.type() == QEvent.Type.Leave:
                self._hide_tooltip()
        return super().eventFilter(obj, event)

    def _show_tooltip(self) -> None:
        """显示工具提示。"""
        if self.tooltip:
            if self._tooltip:
                self._tooltip.close()
            self._tooltip = ToolTip(self.tooltip, self)
            self._tooltip.shadowEffect.setColor(QColor(0, 0, 0, 15))
            self._tooltip.shadowEffect.setOffset(0, 1)
            self._tooltip.setDuration(0)

            # 计算工具提示位置
            label_pos = self.titleLabel.mapToGlobal(self.titleLabel.rect().topLeft())
            x = label_pos.x() - 64
            y = label_pos.y() - self._tooltip.size().height() - 10
            self._tooltip.move(x, y)
            self._tooltip.show()

    def _hide_tooltip(self) -> None:
        """隐藏工具提示。"""
        if self._tooltip:
            self._tooltip.close()
            self._tooltip = None

    def set_options_by_list(self, options: List[ConfigItem]) -> None:
        """通过 ConfigItem 列表设置下拉框选项。"""
        self.combo_box.blockSignals(True)
        self.combo_box.clear()
        self._opts_list.clear()

        for opt_item in options:
            self._opts_list.append(opt_item)
            self.combo_box.addItem(opt_item.ui_text, userData=opt_item.value)

        self.combo_box.blockSignals(False)

    def init_with_adapter(self, adapter: Optional[YamlConfigAdapter]) -> None:
        """初始化配置适配器。"""
        self.adapter = adapter
        self.setValue(None if adapter is None else adapter.get_value(), emit_signal=False)

    def _on_index_changed(self, index: int) -> None:
        """索引变化时发射信号。"""
        if index == self.last_index:
            return

        self.last_index = index
        self._update_desc()
        val = self.combo_box.itemData(index)

        if self.adapter is not None:
            self.adapter.set_value(val)

        self.value_changed.emit(index, val)

    def _update_desc(self) -> None:
        """更新描述显示。"""
        if self.combo_box.currentIndex() >= 0:
            desc = self._opts_list[self.combo_box.currentIndex()].desc
            if desc != self.content:
                self.setContent(desc)

    def setValue(self, value: object, emit_signal: bool = True) -> None:
        """设置下拉框的值。"""
        if not emit_signal:
            self.combo_box.blockSignals(True)

        if value is None:
            self.last_index = -1
            self.combo_box.setCurrentIndex(-1)
        else:
            for idx in range(self.combo_box.count()):
                if self.combo_box.itemData(idx) == value:
                    self.last_index = idx
                    self.combo_box.setCurrentIndex(idx)
                    break

        if not emit_signal:
            self.combo_box.blockSignals(False)
        self._update_desc()

    def getValue(self) -> object:
        """获取当前选中的值。"""
        return self.combo_box.itemData(self.combo_box.currentIndex())
