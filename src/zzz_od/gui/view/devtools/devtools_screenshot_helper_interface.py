from qfluentwidgets import FluentIcon

from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.setting_card.key_setting_card import KeySettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from zzz_od.application.devtools.screenshot_helper.screenshot_helper_app import ScreenshotHelperApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.app_run_interface import AppRunInterface


class DevtoolsScreenshotHelperInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx

        top_widget = ColumnWidget()

        self.frequency_opt = TextSettingCard(icon=FluentIcon.GAME, title='截图间隔(ms)')
        self.frequency_opt.value_changed.connect(self._on_frequency_changed)
        top_widget.add_widget(self.frequency_opt)

        self.length_opt = TextSettingCard(icon=FluentIcon.GAME, title='持续时间(ms)')
        self.length_opt.value_changed.connect(self._on_length_changed)
        top_widget.add_widget(self.length_opt)

        self.key_save_opt = KeySettingCard(icon=FluentIcon.GAME, title='保存截图')
        self.key_save_opt.value_changed.connect(self._on_key_save_changed)
        top_widget.add_widget(self.key_save_opt)

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='devtools_screenshot_helper_interface',
            nav_text_cn='截图助手',
            parent=parent,
            widget_at_top=top_widget
        )

    def init_on_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        AppRunInterface.init_on_shown(self)
        self.frequency_opt.setValue(str(self.ctx.screenshot_helper_config.frequency_second))
        self.length_opt.setValue(str(self.ctx.screenshot_helper_config.length_second))
        self.key_save_opt.setValue(str(self.ctx.screenshot_helper_config.key_save))

    def get_app(self) -> ZApplication:
        return ScreenshotHelperApp(self.ctx)

    def _on_frequency_changed(self, value: str):
        self.ctx.screenshot_helper_config.frequency_second = float(value)

    def _on_length_changed(self, value: str):
        self.ctx.screenshot_helper_config.length_second = float(value)

    def _on_key_save_changed(self, value: str):
        self.ctx.screenshot_helper_config.key_save = value
