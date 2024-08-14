from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon
from typing import Optional, List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.view.app_run_interface import AppRunInterface
from zzz_od.application.hollow_zero.hollow_zero_app import HollowZeroApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.hollow_zero.hollow_zero_challenge_config import get_all_hollow_zero_challenge_config, \
    HollowZeroChallengeConfig


class HollowZeroRunInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx
        self.app: Optional[ZApplication] = None

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='hollow_zero_run_interface',
            nav_text_cn='零号空洞',
            parent=parent,
        )

    def get_widget_at_top(self) -> QWidget:
        top_widget = ColumnWidget()

        self.mission_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='挑战副本')
        self.mission_opt.value_changed.connect(self._on_mission_changed)
        top_widget.add_widget(self.mission_opt)

        self.challenge_config_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='挑战配置')
        self.challenge_config_opt.value_changed.connect(self._on_challenge_config_changed)
        top_widget.add_widget(self.challenge_config_opt)

        return top_widget

    def on_interface_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        AppRunInterface.on_interface_shown(self)
        self._update_mission_options()
        self._update_challenge_config_options()

        self.mission_opt.setValue(self.ctx.hollow_zero_config.mission_name)
        self.challenge_config_opt.setValue(self.ctx.hollow_zero_config.challenge_config)

    def _update_mission_options(self) -> None:
        try:
            # 更新之前 先取消原来的监听 防止触发事件
            self.mission_opt.value_changed.disconnect(self._on_mission_changed)
        except Exception:
            pass
        mission_list: List[str] = self.ctx.compendium_service.get_hollow_zero_mission_name_list()
        opt_list = [
            ConfigItem(mission_name)
            for mission_name in mission_list
        ]
        self.mission_opt.set_options_by_list(opt_list)
        self.mission_opt.value_changed.connect(self._on_mission_changed)

    def _update_challenge_config_options(self) -> None:
        """
        更新已有的yml选项
        :return:
        """
        try:
            # 更新之前 先取消原来的监听 防止触发事件
            self.challenge_config_opt.value_changed.disconnect(self._on_challenge_config_changed)
        except Exception:
            pass
        config_list: List[HollowZeroChallengeConfig] = get_all_hollow_zero_challenge_config()
        opt_list = [
            ConfigItem(config.module_name, config.module_name)
            for config in config_list
        ]
        self.challenge_config_opt.set_options_by_list(opt_list)
        self.challenge_config_opt.value_changed.connect(self._on_challenge_config_changed)

    def _on_mission_changed(self, idx, value) -> None:
        self.ctx.hollow_zero_config.mission_name = value

    def _on_challenge_config_changed(self, idx, value) -> None:
        self.ctx.hollow_zero_config.challenge_config = value
        self.ctx.init_hollow_config()

    def get_app(self) -> ZApplication:
        return HollowZeroApp(self.ctx)
