from concurrent.futures import ThreadPoolExecutor
from typing import Union

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from qfluentwidgets import FluentIconBase

from one_dragon.base.operation.context_base import ContextKeyboardEventEnum
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext


_app_run_interface_executor = ThreadPoolExecutor(thread_name_prefix='app_run_interface', max_workers=1)


class AppRunInterface(VerticalScrollInterface):

    def __init__(self,
                 ctx: ZContext,
                 object_name: str,
                 nav_text_cn: str,
                 nav_icon: Union[FluentIconBase, QIcon, str] = None,
                 parent=None):
        self.ctx = ctx

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        self.start_btn = QPushButton(text='%s %s' % (gt('开始', 'ui'), self.ctx.key_start_running.upper()))
        content_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton(text='%s %s' % (gt('停止', 'ui'), self.ctx.key_stop_running.upper()))
        content_layout.addWidget(self.stop_btn)

        VerticalScrollInterface.__init__(
            self,
            content_widget=content_widget,
            object_name=object_name,
            nav_text_cn=nav_text_cn,
            nav_icon=nav_icon,
            parent=parent
        )

    def init_on_shown(self) -> None:
        self.ctx.listen_event(ContextKeyboardEventEnum.PRESS.value, self._on_key_press)

    def on_hidden(self) -> None:
        self.ctx.unlisten_all_event(self)

    def _on_key_press(self, key: str) -> None:
        """
        按键监听
        """
        if key == self.ctx.key_start_running and self.ctx.is_context_stop:
            _app_run_interface_executor.submit(self.run_app)

    def run_app(self) -> None:
        """
        运行应用 由子类事项
        """
        pass
