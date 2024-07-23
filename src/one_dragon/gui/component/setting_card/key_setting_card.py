from typing import Union, Optional

from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QIcon, Qt
from qfluentwidgets import SettingCard, FluentIconBase, PushButton

from one_dragon.base.controller.pc_button.pc_button_listener import PcButtonListener
from one_dragon.utils.i18_utils import gt


class KeyEventWorker(QObject):

    key_pressed = Signal(str)

    def on_key_press(self, key: str) -> None:
        """
        按键后触发 发送信号
        :param key:
        :return:
        """
        self.key_pressed.emit(key)


class KeySettingCard(SettingCard):

    value_changed = Signal(str)

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title: str, value: str = '',
                 content: Optional[str] = None, parent=None,
                 ):
        """
        更改按键的
        :param icon: 左边显示的图标
        :param title: 左边的标题 中文
        :parma value: 当前值
        :param content: 左侧的详细文本 中文
        :param parent: 组件的parent
        """
        super().__init__(icon, gt(title, 'ui'), gt(content, 'ui'), parent)
        self.value: str = value
        self.btn = PushButton(text=value.upper(), parent=self)
        self.btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn.clicked.connect(self._on_btn_clicked)

        self.button_listener = None  # 监听
        self.key_worker = KeyEventWorker()
        self.key_worker.key_pressed.connect(self._on_key_signal)

        self.hBoxLayout.addWidget(self.btn, 1, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _on_btn_clicked(self) -> None:
        """
        点击按钮后 开始监听按键事件
        :return:
        """
        if self.button_listener is None:
            self.button_listener = PcButtonListener(self._on_key_press, listen_keyboard=True, listen_mouse=True)
            self.btn.setText(gt('请按键', 'ui'))
            self.button_listener.start()
        else:
            self._stop_listener()
            self.btn.setText(self.value.upper())

    def _on_key_press(self, key):
        """
        按键时触发
        :param key:
        :return:
        """
        self._stop_listener()
        self.key_worker.on_key_press(key)

    def _on_key_signal(self, key: str) -> None:
        """
        :param key:
        :return:
        """
        self.setValue(key)
        self.value_changed.emit(key)

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
        self.btn.setText(value.upper())

    def _stop_listener(self) -> None:
        """
        停止键盘鼠标的监听
        :return:
        """
        if self.button_listener is not None:
            self.button_listener.stop()
            self.button_listener = None
