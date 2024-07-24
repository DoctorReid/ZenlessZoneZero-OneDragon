from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import FluentIconBase, PrimaryPushButton, FluentIcon, PushButton, SubtitleLabel
from typing import Union, Optional

from one_dragon.base.operation.application_base import Application
from one_dragon.base.operation.context_event_bus import ContextEventItem
from one_dragon.base.operation.one_dragon_context import ContextKeyboardEventEnum, ContextRunningStateEventEnum, \
    OneDragonContext
from one_dragon.gui.component.app_event_log_display_card import AppEventLogDisplayCard
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.log_display_card import LogDisplayCard
from one_dragon.gui.component.row_widget import RowWidget
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


class AppRunner(QThread):

    state_changed = Signal()

    def __init__(self, ctx: OneDragonContext, app: Optional[Application] = None):
        super().__init__()
        self.ctx: OneDragonContext = ctx
        self.app: Application = app

    def run(self):
        """
        运行 最后发送结束信号
        :return:
        """
        self.ctx.listen_event(ContextRunningStateEventEnum.START_RUNNING.value, self._on_state_changed)
        self.ctx.listen_event(ContextRunningStateEventEnum.PAUSE_RUNNING.value, self._on_state_changed)
        self.ctx.listen_event(ContextRunningStateEventEnum.STOP_RUNNING.value, self._on_state_changed)
        self.ctx.listen_event(ContextRunningStateEventEnum.RESUME_RUNNING.value, self._on_state_changed)

        self.app.execute()

        self.ctx.unlisten_all_event(self)

    def _on_state_changed(self, ignored) -> None:
        """
        运行状态改变
        :return:
        """
        self.state_changed.emit()


class AppRunInterface(VerticalScrollInterface):

    def __init__(self,
                 ctx: OneDragonContext,
                 object_name: str,
                 nav_text_cn: str,
                 nav_icon: Union[FluentIconBase, QIcon, str] = None,
                 parent=None,
                 widget_at_top: Optional[QWidget] = None,
                 widget_at_bottom: Optional[QWidget] = None,
                 app_event_log_card: Optional[AppEventLogDisplayCard] = None
                 ):
        self.ctx = ctx

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if widget_at_top is not None:
            content_layout.addWidget(widget_at_top)

        self.state_text = SubtitleLabel()
        self.state_text.setText('%s %s' % (gt('当前状态', 'ui'), self.ctx.context_running_status_text))
        self.state_text.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        content_layout.addWidget(self.state_text)

        # 按钮行
        btn_row_widget = QWidget()
        btn_row_layout = QHBoxLayout(btn_row_widget)
        content_layout.addWidget(btn_row_widget)

        self.start_btn = PrimaryPushButton(
            text='%s %s' % (gt('开始', 'ui'), self.ctx.key_start_running.upper()),
            icon=FluentIcon.PLAY,
        )
        self.start_btn.clicked.connect(self._on_start_clicked)
        btn_row_layout.addWidget(self.start_btn)

        self.stop_btn = PushButton(
            text='%s %s' % (gt('停止', 'ui'), self.ctx.key_stop_running.upper()),
            icon=FluentIcon.CLOSE
        )
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        btn_row_layout.addWidget(self.stop_btn)

        self.log_card = LogDisplayCard()

        if app_event_log_card is not None:
            log_row = RowWidget()
            content_layout.addWidget(log_row)

            log_row.row_layout.addWidget(self.log_card, stretch=1)

            self.app_event_log_card: AppEventLogDisplayCard = app_event_log_card
            log_row.row_layout.addWidget(app_event_log_card, stretch=1)
        else:
            content_layout.addWidget(self.log_card)

        self.app_runner = AppRunner(self.ctx)
        self.app_runner.state_changed.connect(self._on_context_state_changed)

        if widget_at_bottom is not None:
            content_layout.addWidget(widget_at_bottom)

        content_layout.setStretch(content_layout.count() - 1, 1)

        VerticalScrollInterface.__init__(
            self,
            ctx=ctx,
            content_widget=content_widget,
            object_name=object_name,
            nav_text_cn=nav_text_cn,
            nav_icon=nav_icon,
            parent=parent
        )

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)
        self.log_card.update_on_log = True
        self.ctx.listen_event(ContextKeyboardEventEnum.PRESS.value, self._on_key_press)

    def on_interface_hidden(self) -> None:
        VerticalScrollInterface.on_interface_hidden(self)
        self.log_card.update_on_log = False
        self.ctx.unlisten_all_event(self)

    def _on_key_press(self, event: ContextEventItem) -> None:
        """
        按键监听
        """
        key: str = event.data
        if key == self.ctx.key_start_running and self.ctx.is_context_stop:
            self.run_app()

    def run_app(self) -> None:
        """
        运行应用
        """
        if self.app_runner.isRunning():
            log.error('已有应用在运行中')
            return
        app = self.get_app()
        if app is None:
            log.error('未提供对应应用')
            return
        if self.app_event_log_card is not None:
            self.app_event_log_card.start_listen()
        self.app_runner.app = app
        self.app_runner.start()

    def get_app(self) -> Application:
        """
        获取本次运行的app 由子类实现
        由
        :return:
        """
        pass

    def _on_context_state_changed(self) -> None:
        """
        按运行状态更新显示
        :return:
        """
        if self.ctx.is_context_running:
            text = gt('暂停', 'ui')
            icon = FluentIcon.PAUSE
        elif self.ctx.is_context_pause:
            text = gt('继续', 'ui')
            icon = FluentIcon.PLAY
        else:
            text = gt('开始', 'ui')
            icon = FluentIcon.PLAY

        self.start_btn.setText('%s %s' % (text, self.ctx.key_start_running.upper()))
        self.start_btn.setIcon(icon)
        self.state_text.setText('%s %s' % (gt('当前状态', 'ui'), self.ctx.context_running_status_text))

        if self.app_event_log_card is not None:
            if self.ctx.is_context_stop:
                self.app_event_log_card.stop_listen()
            else:
                self.app_event_log_card.start_listen()

    def _on_start_clicked(self) -> None:
        self.run_app()

    def _on_stop_clicked(self) -> None:
        self.ctx.stop_running()
