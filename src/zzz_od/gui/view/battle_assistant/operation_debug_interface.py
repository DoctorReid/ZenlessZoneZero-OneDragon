import os.path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, PushButton
from typing import Optional

from one_dragon.gui.component.app_event_log_display_card import AppEventLogDisplayCard
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.view.app_run_interface import AppRunInterface
from zzz_od.application.battle_assistant.auto_battle_config import get_auto_battle_config_file_path
from zzz_od.application.battle_assistant.operation_debug_app import OperationDebugApp
from zzz_od.application.battle_assistant.operation_template_config import get_operation_template_config_list
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.config.game_config import GamepadTypeEnum
from zzz_od.context.zzz_context import ZContext


class OperationDebugInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='operation_debug_interface',
            nav_text_cn='指令调试',
            nav_icon=FluentIcon.GAME,
            parent=parent,
        )

    def get_widget_at_top(self) -> QWidget:
        top_widget = ColumnWidget()

        self.config_opt = ComboBoxSettingCard(
            icon=FluentIcon.GAME, title='指令配置',
            content='选择后，运行测试指令是否正常运行。配置文件在 config/auto_battle_operation 文件夹，删除会恢复默认配置')
        self.config_opt.value_changed.connect(self._on_config_changed)
        top_widget.add_widget(self.config_opt)

        self.del_btn = PushButton(text='删除')
        self.config_opt.hBoxLayout.addWidget(self.del_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.config_opt.hBoxLayout.addSpacing(16)
        self.del_btn.clicked.connect(self._on_del_clicked)

        self.repeat_opt = SwitchSettingCard(
            icon=FluentIcon.GAME, title='循环指令',
            content='不断重复指令 确保可以连贯执行'
        )
        self.repeat_opt.value_changed.connect(self._on_repeat_changed)
        top_widget.add_widget(self.repeat_opt)

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
        self.config_opt.setValue(self.ctx.battle_assistant_config.debug_operation_config)
        self.gamepad_type_opt.setValue(self.ctx.battle_assistant_config.gamepad_type)
        self.repeat_opt.setValue(self.ctx.battle_assistant_config.debug_operation_repeat)

    def _update_auto_battle_config_opts(self) -> None:
        """
        更新闪避指令
        :return:
        """
        try:
            self.config_opt.value_changed.disconnect(self._on_config_changed)
        except:
            pass
        self.config_opt.set_options_by_list(get_operation_template_config_list())
        self.config_opt.value_changed.connect(self._on_config_changed)

    def _on_config_changed(self, index, value):
        self.ctx.battle_assistant_config.debug_operation_config = value

    def _on_repeat_changed(self, value: bool) -> None:
        self.ctx.battle_assistant_config.debug_operation_repeat = value

    def get_app(self) -> ZApplication:
        return OperationDebugApp(self.ctx)

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
