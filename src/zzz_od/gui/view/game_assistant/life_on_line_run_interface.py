from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, HyperlinkCard
from typing import Optional

from one_dragon.base.operation.application_base import Application
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.gui.view.app_run_interface import AppRunInterface
from zzz_od.application.life_on_line.life_on_line_app import LifeOnLineApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext


class LifeOnLineRunInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx
        self.app: Optional[ZApplication] = None

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='life_on_line_run_interface',
            nav_text_cn='拿命验收',
            parent=parent,
        )

    def get_widget_at_top(self) -> QWidget:
        content = ColumnWidget()

        self.help_opt = HyperlinkCard(icon=FluentIcon.HELP, title='使用说明', text='前往',
                                      url='https://one-dragon.org/zzz/zh/docs/feat_one_dragon.html')
        self.help_opt.setContent('先看说明 再使用与提问')
        content.add_widget(self.help_opt)

        self.daily_plan_times_opt = TextSettingCard(
            icon=FluentIcon.CALENDAR,  # 选择与时间相关的图标
            title='每日次数',
        )
        content.add_widget(self.daily_plan_times_opt)

        return content

    def on_interface_shown(self) -> None:
        AppRunInterface.on_interface_shown(self)

        self.daily_plan_times_opt.setValue(str(self.ctx.life_on_line_config.daily_plan_times))
        self.daily_plan_times_opt.value_changed.connect(self._on_daily_plan_times_changed)

    def on_interface_hidden(self) -> None:
        AppRunInterface.on_interface_hidden(self)
        self.daily_plan_times_opt.value_changed.disconnect(self._on_daily_plan_times_changed)

    def _on_daily_plan_times_changed(self, value: str) -> None:
        self.ctx.life_on_line_config.daily_plan_times = int(value)

    def get_app(self) -> Application:
        return LifeOnLineApp(self.ctx)
