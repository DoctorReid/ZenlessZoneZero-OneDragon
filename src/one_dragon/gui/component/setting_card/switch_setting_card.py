from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, Qt
from qfluentwidgets import FluentIconBase, SwitchButton, IndicatorPosition
from typing import Union

from one_dragon.gui.component.setting_card.setting_card_base import SettingCardBase
from one_dragon.utils.i18_utils import gt


class SwitchSettingCard(SettingCardBase):

    value_changed = Signal(bool)

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None,
                 on_text_cn: str = '开', off_text_cn: str = '关'):
        """
        复制原 SwitchSettingCard
        封装了些多语言
        去除了 OptionsConfigItem
        :param icon: 左边显示的图标
        :param title: 左边的标题 中文
        :param content: 左侧的详细文本 中文
        :param parent: 组件的parent
        """
        SettingCardBase.__init__(self, icon, title, content, parent=parent)
        self.on_text_cn: str = on_text_cn
        self.off_text_cn: str = off_text_cn

        self.btn = SwitchButton(parent=self, indicatorPos=IndicatorPosition.RIGHT)
        self.btn._offText = gt(off_text_cn, 'ui')
        self.btn._onText = gt(on_text_cn, 'ui')
        self.btn.checkedChanged.connect(self._on_valued_changed)

        self.hBoxLayout.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _on_valued_changed(self, value: bool):
        self.value_changed.emit(value)

    def setValue(self, value: bool):
        self.btn.setChecked(value)
        text = self.on_text_cn if value else self.off_text_cn
        self.btn.setText(gt(text, 'ui'))
