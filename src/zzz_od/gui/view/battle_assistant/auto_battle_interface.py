import os.path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, PushButton
from typing import Optional

from one_dragon.base.operation.context_event_bus import ContextEventItem
from one_dragon.gui.component.app_event_log_display_card import AppEventLogDisplayCard
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.gui.view.app_run_interface import AppRunInterface
from zzz_od.application.battle_assistant.auto_battle_app import AutoBattleApp
from zzz_od.application.battle_assistant.auto_battle_config import get_auto_battle_config_file_path, \
    get_auto_battle_op_config_list
from zzz_od.application.battle_assistant.auto_battle_debug_app import AutoBattleDebugApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.config.game_config import GamepadTypeEnum
from zzz_od.context.zzz_context import ZContext


class AutoBattleInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx
        self.app: Optional[ZApplication] = None

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='auto_battle_interface',
            nav_text_cn='自动战斗',
            nav_icon=FluentIcon.GAME,
            parent=parent,
        )

    def get_widget_at_top(self) -> QWidget:
        top_widget = ColumnWidget()

        self.config_opt = ComboBoxSettingCard(
            icon=FluentIcon.GAME, title='战斗配置',
            content='调试为以当前画面做一次判断执行。配置文件在 config/auto_battle 文件夹，删除会恢复默认配置')
        self.config_opt.value_changed.connect(self._on_auto_battle_config_changed)
        top_widget.add_widget(self.config_opt)

        self.debug_btn = PushButton(text='调试')
        self.config_opt.hBoxLayout.addWidget(self.debug_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.config_opt.hBoxLayout.addSpacing(16)
        self.debug_btn.clicked.connect(self._on_debug_clicked)

        self.del_btn = PushButton(text='删除')
        self.config_opt.hBoxLayout.addWidget(self.del_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.config_opt.hBoxLayout.addSpacing(16)
        self.del_btn.clicked.connect(self._on_del_clicked)

        self.gpu_opt = SwitchSettingCard(icon=FluentIcon.GAME, title='GPU运算',
                                         content='游戏画面掉帧的话 可以不启用 保证截图间隔+推理耗时在50ms内即可')
        self.gpu_opt.value_changed.connect(self._on_gpu_changed)
        top_widget.add_widget(self.gpu_opt)

        self.screenshot_interval_opt = TextSettingCard(icon=FluentIcon.GAME, title='截图间隔(秒)',
                                                       content='游戏画面掉帧的话 可以适当加大截图间隔 保证截图间隔+推理耗时在50ms内即可')
        self.screenshot_interval_opt.value_changed.connect(self._on_screenshot_interval_changed)
        top_widget.add_widget(self.screenshot_interval_opt)

        self.gamepad_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.GAME, title='手柄类型',
            content='需先安装虚拟手柄依赖，参考文档或使用安装器。仅在战斗助手生效。',
            options_enum=GamepadTypeEnum
        )
        self.gamepad_type_opt.value_changed.connect(self._on_gamepad_type_changed)
        top_widget.add_widget(self.gamepad_type_opt)

        return top_widget

    def get_app_event_log_card(self) -> Optional[AppEventLogDisplayCard]:
        return AppEventLogDisplayCard(self.ctx, AutoBattleOperator.get_all_state_event_ids())

    def on_interface_shown(self) -> None:
        """
        界面显示时 进行初始化
        :return:
        """
        AppRunInterface.on_interface_shown(self)
        self._update_auto_battle_config_opts()
        self.config_opt.setValue(self.ctx.battle_assistant_config.auto_battle_config)
        self.gpu_opt.setValue(self.ctx.battle_assistant_config.use_gpu)
        self.screenshot_interval_opt.setValue(str(self.ctx.battle_assistant_config.screenshot_interval))
        self.gamepad_type_opt.setValue(self.ctx.battle_assistant_config.gamepad_type)
        self.debug_btn.setText('%s %s' % (self.ctx.key_debug.upper(), '调试'))
        self.ctx.listen_event(AutoBattleApp.EVENT_OP_LOADED, self._on_op_loaded)

    def _update_auto_battle_config_opts(self) -> None:
        """
        更新闪避指令
        :return:
        """
        try:
            self.config_opt.value_changed.disconnect(self._on_auto_battle_config_changed)
        except:
            pass
        self.config_opt.set_options_by_list(get_auto_battle_op_config_list('auto_battle'))
        self.config_opt.value_changed.connect(self._on_auto_battle_config_changed)

    def _on_auto_battle_config_changed(self, index, value):
        self.ctx.battle_assistant_config.auto_battle_config = value

    def _on_gpu_changed(self, value: bool):
        self.ctx.battle_assistant_config.use_gpu = value

    def _on_screenshot_interval_changed(self, value: str) -> None:
        self.ctx.battle_assistant_config.screenshot_interval = float(value)

    def get_app(self) -> ZApplication:
        return self.app

    def _on_start_clicked(self) -> None:
        """
        正常运行
        """
        self.app = AutoBattleApp(self.ctx)
        AppRunInterface._on_start_clicked(self)

    def _on_debug_clicked(self) -> None:
        """
        调试
        """
        self.app = AutoBattleDebugApp(self.ctx)
        AppRunInterface._on_start_clicked(self)

    def _on_del_clicked(self) -> None:
        """
        删除配置 只删除非 sample 的
        :return:
        """
        item: str = self.config_opt.getValue()
        if item is None:
            return

        path = get_auto_battle_config_file_path('auto_battle', item)
        if os.path.exists(path):
            os.remove(path)

        self._update_auto_battle_config_opts()

    def _on_gamepad_type_changed(self, idx: int, value: str) -> None:
        self.ctx.battle_assistant_config.gamepad_type = value

    def _on_key_press(self, event: ContextEventItem) -> None:
        """
        按键监听
        """
        key: str = event.data
        if key == self.ctx.key_start_running and self.ctx.is_context_stop:
            self._on_start_clicked()
        elif key == self.ctx.key_debug and self.ctx.is_context_stop:
            self._on_debug_clicked()

    def _on_op_loaded(self, event: ContextEventItem) -> None:
        """
        指令加载之后 更新需要监听的事件
        :param event:
        :return:
        """
        if self.app_event_log_card is None:
            return
        self.app_event_log_card.set_target_event_ids(event.data)
