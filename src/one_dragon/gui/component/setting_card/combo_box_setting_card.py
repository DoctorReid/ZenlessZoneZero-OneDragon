from enum import Enum
from typing import Union, Iterable, Optional, List

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, Qt
from qfluentwidgets import SettingCard, FluentIconBase, ComboBox

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.utils.i18_utils import gt


class ComboBoxSettingCard(SettingCard):

    value_changed = Signal(int, object)

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title: str,
                 options_enum: Optional[Iterable[Enum]] = None,
                 options_list: Optional[List[ConfigItem]] = None,
                 content=None, show_config_desc: bool = False, parent=None):
        """
        :param icon: 左边显示的图标
        :param title: 左边的标题 中文
        :param options_enum: 右侧下拉框的选项
        :param content: 左侧的详细文本 中文
        :param parent: 组件的parent
        :param show_config_desc: 显示选项的描述
        """
        super().__init__(icon, gt(title, 'ui'), gt(content, 'ui'), parent)
        self.combo_box = ComboBox(self)
        self.hBoxLayout.addWidget(self.combo_box, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self._opts_list: List[ConfigItem] = []
        self.show_config_desc: bool = show_config_desc  # 显示选项的描述
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

        self.last_index: int = -1  # 上一次选择的下标
        if len(self.combo_box.items) > 0:
            self.combo_box.setCurrentIndex(0)
            self.last_index = 0

        self.combo_box.currentIndexChanged.connect(self._on_index_changed)

    def set_options_by_list(self, options: List[ConfigItem]) -> None:
        """
        设置选项
        :param options:
        :return:
        """
        self.combo_box.setCurrentIndex(-1)
        self.combo_box.clear()
        self._opts_list.clear()
        for opt_item in options:
            self._opts_list.append(opt_item)
            self.combo_box.addItem(opt_item.ui_text, userData=opt_item.value)

    def _on_index_changed(self, index: int) -> None:
        """
        值发生改变时 往外发送信号
        :param index:
        :return:
        """
        if index == self.last_index:  # 没改变时 不发送信号
            return
        self.last_index = index
        self._update_desc()
        self.value_changed.emit(index, self.combo_box.itemData(index))

    def _update_desc(self) -> None:
        """
        更新描述显示
        :return:
        """
        if self.show_config_desc:
            desc = self._opts_list[self.combo_box.currentIndex()].desc
            self.setContent(desc)

    def setContent(self, content: str) -> None:
        """
        更新左侧详细文本
        :param content: 文本 中文
        :return:
        """
        SettingCard.setContent(self, gt(content, 'ui'))

    def setValue(self, value: object) -> None:
        """
        设置值
        :param value:
        :return:
        """
        for idx, item in enumerate(self.combo_box.items):
            if item.userData == value:
                self.combo_box.setCurrentIndex(idx)
                self._update_desc()
                return

    def getValue(self):
        return self.combo_box.itemData(self.combo_box.currentIndex())
