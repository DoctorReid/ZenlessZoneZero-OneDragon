import os.path

from PySide6.QtCore import Qt
from qfluentwidgets import FluentIcon, PushButton

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from zzz_od.application.dodge_assistant.dodge_assistant_app import DodgeAssistantApp
from zzz_od.application.dodge_assistant.dodge_assistant_config import get_dodge_op_config_list, \
    get_dodge_config_file_path
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.app_run_interface import AppRunInterface


class DodgeAssistantInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx

        top_widget = ColumnWidget()

        self.dodge_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='闪避方式',
                                             content='配置文件在 config/dodge 文件夹，删除会恢复默认配置')
        top_widget.add_widget(self.dodge_opt)

        self.del_btn = PushButton(text='删除')
        self.dodge_opt.hBoxLayout.addWidget(self.del_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.dodge_opt.hBoxLayout.addSpacing(16)
        self.del_btn.clicked.connect(self._on_del_clicked)

        self.gpu_opt = SwitchSettingCard(icon=FluentIcon.GAME, title='GPU运算',
                                         content='游戏画面掉帧的话 可以不启用 保证截图间隔+推理耗时在50ms内即可')
        self.gpu_opt.value_changed.connect(self._on_gpu_changed)
        top_widget.add_widget(self.gpu_opt)

        self.screenshot_interval_opt = TextSettingCard(icon=FluentIcon.GAME, title='截图间隔(秒)',
                                                       content='游戏画面掉帧的话 可以适当加大截图间隔 保证截图间隔+推理耗时在50ms内即可')
        self.screenshot_interval_opt.value_changed.connect(self._on_screenshot_interval_changed)
        top_widget.add_widget(self.screenshot_interval_opt)

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='dodge_assistant_interface',
            nav_text_cn='闪避助手',
            nav_icon=FluentIcon.PLAY,
            parent=parent,
            widget_at_top=top_widget
        )

    def on_interface_shown(self) -> None:
        """
        界面显示时 进行初始化
        :return:
        """
        AppRunInterface.on_interface_shown(self)
        self._update_dodge_way_opts()
        self.dodge_opt.setValue(self.ctx.dodge_assistant_config.dodge_way)
        self.gpu_opt.setValue(self.ctx.dodge_assistant_config.use_gpu)
        self.screenshot_interval_opt.setValue(str(self.ctx.dodge_assistant_config.screenshot_interval))

    def _update_dodge_way_opts(self) -> None:
        """
        更新闪避指令
        :return:
        """
        try:
            self.dodge_opt.value_changed.disconnect(self._on_dodge_way_changed)
        except:
            pass
        self.dodge_opt.set_options_by_list(get_dodge_op_config_list())
        self.dodge_opt.value_changed.connect(self._on_dodge_way_changed)

    def _on_dodge_way_changed(self, index, value):
        self.ctx.dodge_assistant_config.dodge_way = value

    def _on_gpu_changed(self, value: bool):
        self.ctx.dodge_assistant_config.use_gpu = value

    def _on_screenshot_interval_changed(self, value: str) -> None:
        self.ctx.dodge_assistant_config.screenshot_interval = float(value)

    def get_app(self) -> ZApplication:
        return DodgeAssistantApp(self.ctx)

    def _on_del_clicked(self) -> None:
        """
        删除配置
        :return:
        """
        item: str = self.dodge_opt.getValue()
        if item is None:
            return

        path = get_dodge_config_file_path(item)
        if os.path.exists(path):
            os.remove(path)

        self._update_dodge_way_opts()
