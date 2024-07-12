from qfluentwidgets import FluentIcon

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from zzz_od.application.dodge_assistant.dodge_assistant_app import DodgeAssistantApp
from zzz_od.application.dodge_assistant.dodge_assistant_config import DodgeWayEnum
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.app_run_interface import AppRunInterface


class DodgeAssistantInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx

        self.dodge_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='闪避方式', options=DodgeWayEnum)
        self.dodge_opt.value_changed.connect(self._on_dodge_way_changed)

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='dodge_assistant,interface',
            nav_text_cn='闪避助手',
            nav_icon=FluentIcon.PLAY,
            parent=parent,
            widget_at_top=self.dodge_opt
        )

    def init_on_shown(self) -> None:
        """
        界面显示时 进行初始化
        :return:
        """
        AppRunInterface.init_on_shown(self)
        dodge_way = get_config_item_from_enum(DodgeWayEnum, self.ctx.dodge_assistant_config.dodge_way)
        if dodge_way is not None:
            self.dodge_opt.setValue(dodge_way.value)

    def _on_dodge_way_changed(self, index, value):
        config_item = get_config_item_from_enum(DodgeWayEnum, value)
        self.ctx.dodge_assistant_config.dodge_way = config_item.value

    def get_app(self) -> ZApplication:
        return DodgeAssistantApp(self.ctx)
