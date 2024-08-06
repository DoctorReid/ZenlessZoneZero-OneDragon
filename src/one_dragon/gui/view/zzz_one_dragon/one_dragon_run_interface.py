from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from enum import Enum
from qfluentwidgets import FluentIcon, SettingCardGroup, SubtitleLabel, PrimaryPushButton, PushButton
from typing import List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.operation.application_base import Application, ApplicationEventId
from one_dragon.base.operation.context_event_bus import ContextEventItem
from one_dragon.base.operation.one_dragon_app import OneDragonApp
from one_dragon.base.operation.one_dragon_context import OneDragonContext, ContextRunningStateEventEnum, \
    ContextKeyboardEventEnum
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.log_display_card import LogDisplayCard
from one_dragon.gui.component.setting_card.app_run_card import AppRunCard
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.utils import cmd_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from one_dragon.gui.view.app_run_interface import AppRunner


class AfterDoneOpEnum(Enum):

    NONE = ConfigItem('无', 'none')
    CLOSE_GAME = ConfigItem('关闭游戏', 'close_game')
    SHUTDOWN = ConfigItem('关机', 'shutdown')


class OneDragonRunInterface(VerticalScrollInterface):

    def __init__(self, ctx: OneDragonContext, one_dragon_app: OneDragonApp, parent=None):
        self.one_dragon_app: OneDragonApp = one_dragon_app

        VerticalScrollInterface.__init__(
            self,
            ctx=ctx,
            content_widget=None,
            nav_icon=FluentIcon.BUS,
            object_name='one_dragon_run_interface',
            parent=parent,
            nav_text_cn='一条龙运行'
        )

        self._app_run_cards: List[AppRunCard] = []

    def get_content_widget(self) -> QWidget:
        """
        子界面内的内容组件 由子类实现
        :return:
        """
        content_widget = QWidget()
        # 创建 QVBoxLayout 作为主布局
        main_layout = QVBoxLayout(content_widget)

        # 创建 QHBoxLayout 作为中间布局
        horizontal_layout = QHBoxLayout()

        # 将 QVBoxLayouts 加入 QHBoxLayout
        horizontal_layout.addLayout(self._get_left_layout(), stretch=1)
        horizontal_layout.addLayout(self._get_right_layout(), stretch=1)

        # 确保 QHBoxLayout 可以伸缩
        horizontal_layout.setSpacing(0)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # 设置伸缩因子，让 QHBoxLayout 占据空间
        main_layout.addLayout(horizontal_layout, stretch=1)

        self.app_runner = AppRunner(self.ctx)
        self.app_runner.state_changed.connect(self._on_context_state_changed)

        return content_widget

    def _get_left_layout(self) -> QVBoxLayout:
        """
        左边的布局
        :return:
        """
        layout = QVBoxLayout()
        self.app_card_group = SettingCardGroup(gt('任务列表', 'ui'))
        layout.addWidget(self.app_card_group)

        return layout

    def _get_right_layout(self) -> QVBoxLayout:
        """
        右边的布局
        :return:
        """
        layout = QVBoxLayout()
        layout.setSpacing(5)

        run_group = SettingCardGroup(gt('运行设置', 'ui'))
        layout.addWidget(run_group)

        self.after_done_opt = ComboBoxSettingCard(icon=FluentIcon.CALENDAR, title='结束后',
                                                  options_enum=AfterDoneOpEnum)
        self.after_done_opt.value_changed.connect(self._on_after_done_changed)
        run_group.addSettingCard(self.after_done_opt)

        self.state_text = SubtitleLabel()
        self.state_text.setText('%s %s' % (gt('当前状态', 'ui'), self.ctx.context_running_status_text))
        self.state_text.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.state_text)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(5)
        layout.addLayout(btn_row)

        self.start_btn = PrimaryPushButton(
            text='%s %s' % (gt('开始', 'ui'), self.ctx.key_start_running.upper()),
            icon=FluentIcon.PLAY,
        )
        self.start_btn.clicked.connect(self._on_start_clicked)
        btn_row.addWidget(self.start_btn, stretch=1)

        self.stop_btn = PushButton(
            text='%s %s' % (gt('停止', 'ui'), self.ctx.key_stop_running.upper()),
            icon=FluentIcon.CLOSE
        )
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        btn_row.addWidget(self.stop_btn, stretch=1)

        self.log_card = LogDisplayCard()
        layout.addWidget(self.log_card, stretch=1)

        return layout

    def _init_app_list(self) -> None:
        """
        初始化应用列表
        :return:
        """
        if not self.ctx.is_context_stop:  # 不是停止状态不更新
            return
        self.app_list = self.one_dragon_app.get_one_dragon_apps_in_order()
        app_run_list = self.ctx.one_dragon_config.app_run_list

        if len(self._app_run_cards) > 0:  # 之前已经添加了组件了 这次只是调整顺序
            for idx, app in enumerate(self.app_list):
                self._app_run_cards[idx].set_app(app)
        else:
            for app in self.app_list:
                app_run_card = AppRunCard(app, switch_on=app.app_id in app_run_list)
                self._app_run_cards.append(app_run_card)
                self.app_card_group.addSettingCard(app_run_card)
                app_run_card.update_display()

                app_run_card.move_up.connect(self._on_app_card_move_up)
                app_run_card.run.connect(self._on_app_card_run)
                app_run_card.switched.connect(self._on_app_switch_run)

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)
        self._init_app_list()
        self.log_card.set_update_log(True)
        self.ctx.listen_event(ContextKeyboardEventEnum.PRESS.value, self._on_key_press)
        self.ctx.listen_event(ApplicationEventId.APPLICATION_START.value, self._on_app_state_changed)
        self.ctx.listen_event(ApplicationEventId.APPLICATION_STOP.value, self._on_app_state_changed)

    def on_interface_hidden(self) -> None:
        VerticalScrollInterface.on_interface_hidden(self)
        self.log_card.set_update_log(False)
        self.ctx.unlisten_all_event(self)

    def _on_after_done_changed(self, value: str) -> None:
        """
        结束后的操作
        :param value:
        :return:
        """
        if value != AfterDoneOpEnum.SHUTDOWN.value.value:
            log.info('已取消关机计划')
            cmd_utils.cancel_shutdown_sys()

    def run_app(self, app: Application) -> None:
        self.app_runner.app = app
        self.app_runner.start()

    def _on_start_clicked(self) -> None:
        self.run_app(self.one_dragon_app)

    def _on_stop_clicked(self) -> None:
        self.ctx.stop_running()

    def _on_key_press(self, event: ContextEventItem) -> None:
        """
        按键监听
        """
        key: str = event.data
        if key == self.ctx.key_start_running and self.ctx.is_context_stop:
            self.run_app(self.one_dragon_app)

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

        for app_card in self._app_run_cards:
            app_card.update_display()

    def _on_app_state_changed(self, event) -> None:
        for app_card in self._app_run_cards:
            app_card.update_display()

    def _on_app_card_move_up(self, app_id: str) -> None:
        """
        将该应用往上调整一位
        :param app_id:
        :return:
        """
        self.ctx.one_dragon_config.move_up_app(app_id)
        self._init_app_list()

    def _on_app_card_run(self, app_id: str) -> None:
        """
        运行某个特殊的应用
        :param app_id:
        :return:
        """
        for app in self.app_list:
            if app.app_id == app_id:
                self.run_app(app)

    def _on_app_switch_run(self, app_id: str, value: bool) -> None:
        """
        应用运行状态切换
        :param app_id:
        :param value:
        :return:
        """
        self.ctx.one_dragon_config.set_app_run(app_id, value)