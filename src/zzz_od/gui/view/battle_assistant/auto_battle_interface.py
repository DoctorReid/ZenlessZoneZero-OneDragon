import os.path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, PushButton

from one_dragon.base.operation.context_event_bus import ContextEventItem
from one_dragon.gui.component.app_event_log_display_card import AppEventLogDisplayCard
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.gui.view.app_run_interface import AppRunInterface
from zzz_od.application.battle_assistant.auto_battle_app import AutoBattleApp
from zzz_od.application.battle_assistant.auto_battle_config import get_auto_battle_config_file_path, get_auto_battle_op_config_list
from zzz_od.application.battle_assistant.auto_battle_debug_app import AutoBattleDebugApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.config.game_config import GamepadTypeEnum
from zzz_od.context.zzz_context import ZContext


class AutoBattleInterface(AppRunInterface):
    def __init__(self, ctx: ZContext, parent=None):
        """初始化 AutoBattleInterface 类"""
        self.ctx: ZContext = ctx
        self.app: Optional[ZApplication] = None

        super().__init__(ctx=ctx, object_name='auto_battle_interface', nav_text_cn='自动战斗', nav_icon=FluentIcon.GAME, parent=parent)

        self.config_opt: Optional[ComboBoxSettingCard] = None
        self.gpu_opt: Optional[SwitchSettingCard] = None
        self.screenshot_interval_opt: Optional[TextSettingCard] = None
        self.gamepad_type_opt: Optional[ComboBoxSettingCard] = None
        self.debug_btn: Optional[PushButton] = None
        self.del_btn: Optional[PushButton] = None

    def get_widget_at_top(self) -> QWidget:
        """获取界面顶部的 Widget"""

        top_widget = ColumnWidget()
        self._create_config_option(top_widget)
        self._create_gpu_option(top_widget)
        self._create_screenshot_interval_option(top_widget)
        self._create_gamepad_type_option(top_widget)
        return top_widget


    def get_app_event_log_card(self) -> Optional[AppEventLogDisplayCard]:
        """获取应用事件日志卡片"""
        return AppEventLogDisplayCard(self.ctx, AutoBattleOperator.get_all_state_event_ids())

    def on_interface_shown(self) -> None:
        """界面显示时的处理"""
        super().on_interface_shown()
        self._update_auto_battle_config_opts()
        self._set_initial_values()
        self._update_debug_button_text()
        self.ctx.listen_event(AutoBattleApp.EVENT_OP_LOADED, self._on_op_loaded)

    def _create_config_option(self, parent: QWidget) -> None:
        """创建自动战斗配置选项组件"""
        self.config_opt = ComboBoxSettingCard(
            icon=FluentIcon.GAME, title='战斗配置',
            content='调试为以当前画面做一次判断执行。配置文件在 config/auto_battle 文件夹，删除会恢复默认配置',
            show_tooltip=True
        )
        self.config_opt.value_changed.connect(self._on_auto_battle_config_changed)
        parent.add_widget(self.config_opt)

        self._create_debug_and_delete_buttons()

    def _create_debug_and_delete_buttons(self) -> None:
        """创建调试和删除按钮"""
        self.debug_btn = PushButton(text='调试')
        self.config_opt.hBoxLayout.addWidget(self.debug_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.config_opt.hBoxLayout.addSpacing(16)
        self.debug_btn.clicked.connect(self._on_debug_clicked)

        self.del_btn = PushButton(text='删除')
        self.config_opt.hBoxLayout.addWidget(self.del_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.config_opt.hBoxLayout.addSpacing(16)
        self.del_btn.clicked.connect(self._on_del_clicked)

    def _create_gpu_option(self, parent: QWidget) -> None:
        """创建 GPU 运算开关组件"""
        self.gpu_opt = SwitchSettingCard(
            icon=FluentIcon.GAME, title='GPU运算',
            content='游戏画面掉帧的话可以不启用，保证截图间隔+推理耗时在50ms内即可'
        )
        self.gpu_opt.value_changed.connect(self._on_gpu_changed)
        parent.add_widget(self.gpu_opt)

    def _create_screenshot_interval_option(self, parent: QWidget) -> None:
        """创建截图间隔设置组件"""
        self.screenshot_interval_opt = TextSettingCard(
            icon=FluentIcon.GAME, title='截图间隔(秒)',
            content='游戏画面掉帧的话可以适当加大截图间隔，保证截图间隔+推理耗时在50ms内即可'
        )
        self.screenshot_interval_opt.value_changed.connect(self._on_screenshot_interval_changed)
        parent.add_widget(self.screenshot_interval_opt)

    def _create_gamepad_type_option(self, parent: QWidget) -> None:
        """创建手柄类型选择组件"""
        self.gamepad_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.GAME, title='手柄类型',
            content='需先安装虚拟手柄依赖，参考文档或使用安装器。仅在战斗助手生效。',
            options_enum=GamepadTypeEnum
        )
        self.gamepad_type_opt.value_changed.connect(self._on_gamepad_type_changed)
        parent.add_widget(self.gamepad_type_opt)

    def _update_auto_battle_config_opts(self) -> None:
        """更新自动战斗配置选择组件的选项"""
        try:
            self.config_opt.value_changed.disconnect(self._on_auto_battle_config_changed)
        except Exception:
            pass

        self.config_opt.set_options_by_list(get_auto_battle_op_config_list('auto_battle'))
        self.config_opt.value_changed.connect(self._on_auto_battle_config_changed)

    def _set_initial_values(self) -> None:
        """设置各组件的初始值"""
        self.config_opt.setValue(self.ctx.battle_assistant_config.auto_battle_config)
        self.gpu_opt.setValue(self.ctx.battle_assistant_config.use_gpu)
        self.screenshot_interval_opt.setValue(str(self.ctx.battle_assistant_config.screenshot_interval))
        self.gamepad_type_opt.setValue(self.ctx.battle_assistant_config.gamepad_type)

    def _update_debug_button_text(self) -> None:
        """更新调试按钮的文本显示"""
        self.debug_btn.setText(f'{self.ctx.key_debug.upper()} 调试')

    def _on_auto_battle_config_changed(self, index, value):
        """处理自动战斗配置改变事件"""
        self.ctx.battle_assistant_config.auto_battle_config = value

    def _on_gpu_changed(self, value: bool):
        """处理 GPU 运算开关改变事件"""
        self.ctx.battle_assistant_config.use_gpu = value

    def _on_screenshot_interval_changed(self, value: str) -> None:
        """处理截图间隔改变事件"""
        self.ctx.battle_assistant_config.screenshot_interval = float(value)

    def get_app(self) -> ZApplication:
        """获取当前应用实例"""
        return self.app

    def _on_start_clicked(self) -> None:
        """启动自动战斗"""
        self.app = AutoBattleApp(self.ctx)
        super()._on_start_clicked()

    def _on_debug_clicked(self) -> None:
        """启动自动战斗调试"""
        self.app = AutoBattleDebugApp(self.ctx)
        super()._on_start_clicked()

    def _on_del_clicked(self) -> None:
        """删除自动战斗配置"""
        item: str = self.config_opt.getValue()
        if item:
            path = get_auto_battle_config_file_path('auto_battle', item)
            if os.path.exists(path):
                os.remove(path)
            self._update_auto_battle_config_opts()

    def _on_gamepad_type_changed(self, idx: int, value: str) -> None:
        """处理手柄类型改变事件"""
        self.ctx.battle_assistant_config.gamepad_type = value

    def _on_key_press(self, event: ContextEventItem) -> None:
        """处理键盘事件"""
        key: str = event.data
        if key == self.ctx.key_start_running and self.ctx.is_context_stop:
            self._on_start_clicked()
        elif key == self.ctx.key_debug and self.ctx.is_context_stop:
            self._on_debug_clicked()

    def _on_op_loaded(self, event: ContextEventItem) -> None:
        """处理自动战斗操作加载事件"""
        if self.app_event_log_card:
            self.app_event_log_card.set_target_event_ids(event.data)
