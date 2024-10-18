from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtGui import QIcon, QColor
from enum import Enum
from qfluentwidgets import SettingCard, FluentIconBase, ComboBox, ToolTip
from typing import Union, Iterable, Optional, List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.gui.component.layout_utils import IconSize, Margins
from one_dragon.gui.component.setting_card.setting_card_base import SettingCardBase
from one_dragon.gui.component.setting_card.yaml_config_adapter import YamlConfigAdapter
from one_dragon.utils.i18_utils import gt


class ComboBoxSettingCard(SettingCardBase):
    """
    自定义设置卡片类，包含一个下拉框
    """
    value_changed = Signal(int, object)

    def __init__(self,  title: str,
                 icon: Union[str, QIcon, FluentIconBase] = None,
                 iconSize: IconSize = IconSize(16, 16),
                 margins: Margins = Margins(16, 16, 0, 16),
                 options_enum: Optional[Iterable[Enum]] = None,
                 options_list: Optional[List[ConfigItem]] = None,
                 content=None, show_config_desc: bool = False,
                 show_tooltip: bool = False, parent=None,
                 adapter: Optional[YamlConfigAdapter] = None):
        """
        初始化函数  
        **icon**: 左侧显示的图标  
        **iconSize**: 左侧图标的大小  
        **margins**: 上下左右的间距  
        **title**: 左侧的标题，支持中文  
        **options_enum**: 右侧下拉框的选项，使用枚举类型  
        **options_list**: 右侧下拉框的选项，使用ConfigItem列表  
        **content**: 左侧的详细文本，支持中文  
        **show_config_desc**: 是否显示选项的描述  
        **show_tooltip**: 是否在标题上显示提示  
        **parent**: 组件的父对象  
        **adapter**: 配置适配器 自动更新对应配置文件  
        """
        self.show_tooltip = show_tooltip  # 由于里面会调用setContent 这个需要提前初始化
        SettingCardBase.__init__(self,title,icon,iconSize,margins,content, parent)
        self.adapter: YamlConfigAdapter = adapter

        self.combo_box = ComboBox(self)
        self.hBoxLayout.addWidget(self.combo_box, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.show_config_desc = show_config_desc

        self.tooltip_text = content
        self.tooltip: Optional[ToolTip] = None

        if self.show_tooltip and content:
            self.titleLabel.installEventFilter(self)
        elif content:
            self.setContent(content)

        self._opts_list: List[ConfigItem] = []
        if options_enum is not None:
            for opt in options_enum:
                if not isinstance(opt.value, ConfigItem):
                    continue
                opt_item: ConfigItem = opt.value
                self._opts_list.append(opt_item)
                self.combo_box.addItem(opt_item.ui_text, userData=opt_item.value)
        elif options_list is not None:
            for opt_item in options_list:
                self._opts_list.append(opt_item)
                self.combo_box.addItem(opt_item.ui_text, userData=opt_item.value)

        self.last_index: int = -1
        if len(self.combo_box.items) > 0:
            self.combo_box.setCurrentIndex(0)
            self.last_index = 0

        self.combo_box.currentIndexChanged.connect(self._on_index_changed)

    def eventFilter(self, obj, event: QEvent) -> bool:
        """
        事件过滤器，处理鼠标进入和离开标题标签的事件
        :param obj: 事件对象
        :param event: 事件类型
        :return: 是否处理事件
        """
        if obj == self.titleLabel:
            if event.type() == QEvent.Type.Enter:
                if self.tooltip_text:
                    if self.tooltip:
                        self.tooltip.close()
                    self.tooltip = ToolTip(self.tooltip_text, self)
                    self.tooltip.shadowEffect.setColor(QColor(0, 0, 0, 15))
                    self.tooltip.shadowEffect.setOffset(0, 1)
                    self.tooltip.setDuration(0)
                    label_pos = self.titleLabel.mapToGlobal(self.titleLabel.rect().topLeft())
                    tooltip_height = self.tooltip.size().height()
                    x = label_pos.x() - 64
                    y = label_pos.y() - tooltip_height - 10
                    self.tooltip.move(x, y)
                    self.tooltip.show()
            elif event.type() == QEvent.Type.Leave:
                if self.tooltip:
                    self.tooltip.close()
                    self.tooltip = None
            elif event.type() == QEvent.Type.ToolTip:
                return True
        return super().eventFilter(obj, event)

    def set_options_by_list(self, options: List[ConfigItem]) -> None:
        """
        通过ConfigItem列表设置下拉框选项
        :param options: ConfigItem列表
        """
        self.combo_box.blockSignals(True)
        self.combo_box.setCurrentIndex(-1)
        self.combo_box.clear()
        self._opts_list.clear()
        for opt_item in options:
            self._opts_list.append(opt_item)
            self.combo_box.addItem(opt_item.ui_text, userData=opt_item.value)
        self.combo_box.blockSignals(False)

    def init_with_adapter(self, adapter: Optional[YamlConfigAdapter]) -> None:
        """
        初始化值
        """
        self.adapter = adapter
        if self.adapter is None:
            self.setValue(None, emit_signal=False)
        else:
            self.setValue(self.adapter.get_value(), emit_signal=False)

    def _on_index_changed(self, index: int) -> None:
        """
        当下拉框选项改变时触发，向外发送信号
        :param index: 当前选中的索引
        """
        if index == self.last_index:
            return
        self.last_index = index
        self._update_desc()
        val = self.combo_box.itemData(index)
        self.value_changed.emit(index, val)

        if self.adapter is not None:
            self.adapter.set_value(val)

    def _update_desc(self) -> None:
        """
        更新描述显示
        """
        if self.show_config_desc:
            desc = self._opts_list[self.combo_box.currentIndex()].desc
            self.setContent(desc)

    def setContent(self, content: str) -> None:
        """
        更新左侧详细文本
        :param content: 文本内容，支持中文
        """
        if not self.show_tooltip:
            SettingCard.setContent(self, gt(content, 'ui'))
        else:
            self.tooltip_text = gt(content, 'ui')

    def setValue(self, value: object, emit_signal: bool = True) -> None:
        """
        设置下拉框的值
        :param value: 要设置的值
        """
        if not emit_signal:
            self.combo_box.blockSignals(True)

        if value is None:
            self.last_index = -1
            self.combo_box.setCurrentIndex(-1)
            self._update_desc()
        else:
            for idx, item in enumerate(self.combo_box.items):
                if item.userData == value:
                    self.last_index = idx
                    self.combo_box.setCurrentIndex(idx)
                    self._update_desc()
                    break
        if not emit_signal:
            self.combo_box.blockSignals(False)

    def getValue(self):
        """
        获取当前选中的值
        :return: 当前选中的值
        """
        return self.combo_box.itemData(self.combo_box.currentIndex())