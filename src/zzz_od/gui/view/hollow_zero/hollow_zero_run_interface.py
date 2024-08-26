from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout
from qfluentwidgets import FluentIcon,PushSettingCard,FluentThemeColor
from typing import Optional, List
from PySide6.QtGui import Qt,QColor
from one_dragon.base.config.config_item import ConfigItem
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.gui.view.app_run_interface import AppRunInterface
from zzz_od.application.hollow_zero.hollow_zero_app import HollowZeroApp
from zzz_od.application.hollow_zero.hollow_zero_debug_app import HollowZeroDebugApp
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
        # 创建一个容器 widget 用于水平排列
        col_widget = QWidget(self)
        col_layout = QHBoxLayout(col_widget)
        col_widget.setLayout(col_layout)

        # 创建左侧的垂直布局容器
        left_widget = QWidget(self)
        left_layout = QVBoxLayout(left_widget)
        left_widget.setLayout(left_layout)

        # 创建右侧的垂直布局容器
        right_widget = QWidget(self)
        right_layout = QVBoxLayout(right_widget)
        right_widget.setLayout(right_layout)

        # 创建一个组合框设置卡片，标题为“挑战副本”
        self.mission_opt = ComboBoxSettingCard(
            icon=FluentIcon.GAME,  # 选择与挑战相关的图标
            title='挑战副本', 
            content='选择空洞及难度等级',
        )
        self.mission_opt.setIconSize(24,24)
        self.mission_opt.value_changed.connect(self._on_mission_changed)
        left_layout.addWidget(self.mission_opt)

        # 创建一个文本设置卡片，标题为“每周通关次数”
        self.weekly_times_opt = TextSettingCard(
            icon=FluentIcon.CALENDAR,  # 选择与时间相关的图标
            title='每周通关次数', 
            content='每周完成的通关次数',
        )
        self.weekly_times_opt.setIconSize(24,24)
        self.weekly_times_opt.value_changed.connect(self._on_weekly_times_changed)
        right_layout.addWidget(self.weekly_times_opt)

        # 创建一个组合框设置卡片，标题为“挑战配置”
        self.challenge_config_opt = ComboBoxSettingCard(
            icon=FluentIcon.SETTING,  # 选择与设置相关的图标
            title='挑战配置', 
            content='选择角色、鸣徽和事件',
        )
        self.challenge_config_opt.setIconSize(24,24)
        self.challenge_config_opt.value_changed.connect(self._on_challenge_config_changed)
        left_layout.addWidget(self.challenge_config_opt)

        # 创建一个推送设置卡片，标题为“调试”
        self.debug_opt = PushSettingCard(
            text='调试', 
            icon=FluentIcon.STOP_WATCH,  # 选择与停止相关的图标
            title='调试', 
            content='在中断/停止状态下用于继续执行',
        )
        self.debug_opt.setIconSize(24,24)
        self.debug_opt.clicked.connect(self._on_debug_clicked)
        right_layout.addWidget(self.debug_opt)

        # 将左侧和右侧的 widget 添加到主布局中，并均分空间
        col_layout.addWidget(left_widget, stretch=1)
        col_layout.addWidget(right_widget, stretch=1)

        return col_widget

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
        self.weekly_times_opt.setValue(str(self.ctx.hollow_zero_config.weekly_times))

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
        return self.app

    def _on_start_clicked(self) -> None:
        """
        正常运行
        """
        self.app = HollowZeroApp(self.ctx)
        AppRunInterface._on_start_clicked(self)

    def _on_debug_clicked(self) -> None:
        """
        调试
        """
        self.app = HollowZeroDebugApp(self.ctx)
        self.ctx.hollow.data_service.reload()
        AppRunInterface._on_start_clicked(self)

    def _on_weekly_times_changed(self, value: str) -> None:
        self.ctx.hollow_zero_config.weekly_times = int(value)
