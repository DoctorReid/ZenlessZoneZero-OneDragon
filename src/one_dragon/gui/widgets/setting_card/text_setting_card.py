from PySide6.QtCore import Signal, Qt
from dataclasses import dataclass
from qfluentwidgets import LineEdit, PushButton
from PySide6.QtWidgets import QHBoxLayout
from typing import Optional

from one_dragon.gui.widgets.setting_card.setting_card_base import SettingCardBase
from one_dragon.gui.widgets.setting_card.yaml_config_adapter import YamlConfigAdapter
from one_dragon.utils.i18_utils import gt


@dataclass(eq=False)
class TextSettingCard(SettingCardBase):
    """带文本输入框的设置卡片类"""

    title: str
    input_placeholder: Optional[str] = None
    input_max_width: int = 300
    adapter: Optional[YamlConfigAdapter] = None
    is_password: bool = False  # 新增参数，控制是否为密码模式

    value_changed = Signal(str)

    def __post_init__(self):
        # 初始化父类
        SettingCardBase.__post_init__(self)

        # 创建输入框控件
        self.line_edit = LineEdit(self)
        self.line_edit.setMaximumWidth(self.input_max_width)
        self.line_edit.setPlaceholderText(self.input_placeholder)
        self.line_edit.setClearButtonEnabled(True)

        # 设置密码模式
        if self.is_password:
            self.line_edit.setEchoMode(LineEdit.Password)

            # 添加切换显示/隐藏明文的按钮
            self.toggle_button = PushButton("👁")  # 使用眼睛符号作为图标
            self.toggle_button.setCheckable(True)
            self.toggle_button.setFlat(True)  # 扁平样式
            self.toggle_button.setFixedSize(40, 32)  # 固定按钮大小
            self.toggle_button.clicked.connect(self._toggle_password_visibility)

            # 创建一个水平布局，将输入框和按钮放在一起
            self.input_layout = QHBoxLayout()
            self.input_layout.setContentsMargins(0, 0, 0, 0)  # 去掉内边距
            self.input_layout.addWidget(self.line_edit)  # 左侧为输入框
            self.input_layout.addWidget(self.toggle_button)  # 右侧为按钮

            # 将水平布局添加到卡片的主布局中
            self.hBoxLayout.addLayout(self.input_layout, 1)
        else:
            # 如果不是密码模式，仅添加输入框
            self.hBoxLayout.addWidget(self.line_edit, 1)

        # 添加额外的间距（如果需要）
        self.hBoxLayout.addSpacing(16)

        # 绑定输入框内容变化信号
        self.line_edit.editingFinished.connect(self._on_text_changed)

    def _toggle_password_visibility(self):
        """切换密码显示模式"""
        if self.toggle_button.isChecked():
            self.line_edit.setEchoMode(LineEdit.Normal)  # 显示明文
        else:
            self.line_edit.setEchoMode(LineEdit.Password)  # 隐藏明文

    def _on_text_changed(self) -> None:
        """处理文本更改事件"""
        val = self.line_edit.text()

        if self.adapter is not None:
            self.adapter.set_value(val)

        self.value_changed.emit(val)

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


