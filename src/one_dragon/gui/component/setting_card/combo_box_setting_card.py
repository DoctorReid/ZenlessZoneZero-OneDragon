from enum import Enum
from typing import Union, Iterable

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, Qt
from qfluentwidgets import SettingCard, FluentIconBase, ComboBox

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.utils.i18_utils import gt


class ComboBoxSettingCard(SettingCard):

    value_changed = Signal(int, object)

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title: str, options: Iterable[Enum], content=None, parent=None):
        """
        :param icon: 左边显示的图标
        :param title: 左边的标题 中文
        :param options: 右侧下拉框的选项
        :param content: 左侧的详细文本 中文
        :param parent: 组件的parent
        """
        super().__init__(icon, gt(title, 'ui'), gt(content, 'ui'), parent)
        self.combo_box = ComboBox(self)
        self.hBoxLayout.addWidget(self.combo_box, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        for opt in options:
            if not isinstance(opt.value, ConfigItem):
                continue
            opt_item: ConfigItem = opt.value
            self.combo_box.addItem(opt_item.ui_text, userData=opt_item.value)

        self.last_index: int = -1  # 上一次选择的下标
        if len(self.combo_box.items) > 0:
            self.combo_box.setCurrentIndex(0)
            self.last_index = 0

        self.combo_box.currentIndexChanged.connect(self._on_index_changed)

    def _on_index_changed(self, index: int) -> None:
        """
        值发生改变时 往外发送信号
        :param index:
        :return:
        """
        if index == self.last_index:  # 没改变时 不发送信号
            return
        self.last_index = index
        self.value_changed.emit(index, self.combo_box.itemData(index))

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
                return

    def getValue(self):
        return self.combo_box.itemData(self.combo_box.currentIndex())