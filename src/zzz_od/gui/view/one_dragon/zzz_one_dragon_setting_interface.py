import os
from PySide6.QtWidgets import QWidget, QFileDialog
from qfluentwidgets import SettingCardGroup, FluentIcon, PushSettingCard

from one_dragon.base.config.config_item import get_config_item_from_enum, ConfigItem
from one_dragon.base.controller.pc_button.ds4_button_controller import Ds4ButtonEnum
from one_dragon.base.controller.pc_button.xbox_button_controller import XboxButtonEnum
from one_dragon.gui.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.widgets.setting_card.key_setting_card import KeySettingCard
from one_dragon.gui.widgets.setting_card.text_setting_card import TextSettingCard
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from zzz_od.config.game_config import GameRegionEnum, GamepadTypeEnum
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import AgentEnum

from phosdeiz.gui.widgets import Column


class ZOneDragonSettingInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='zzz_one_dragon_setting_interface',
            content_widget=None, parent=parent,
            nav_text_cn='其他设置'
        )
        self.ctx: ZContext = ctx

    def get_content_widget(self) -> QWidget:
        content_widget = Column()

        self.random_play_agent_1 = ComboBoxSettingCard(
            icon=FluentIcon.PEOPLE, title=gt('影像店代理人-1'),
            options_list=[ConfigItem(self.ctx.random_play_config.random_agent_name())] + [
                ConfigItem(agent_enum.value.agent_name)
                for agent_enum in AgentEnum
            ],
        )
        content_widget.add_widget(self.random_play_agent_1)

        self.random_play_agent_2 = ComboBoxSettingCard(
            icon=FluentIcon.PEOPLE, title=gt('影像店代理人-2'),
            options_list=[ConfigItem(self.ctx.random_play_config.random_agent_name())] + [
                ConfigItem(agent_enum.value.agent_name)
                for agent_enum in AgentEnum
            ],
        )
        content_widget.add_widget(self.random_play_agent_2)

        content_widget.add_stretch(1)

        return content_widget

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.random_play_agent_1.init_with_adapter(self.ctx.random_play_config.agent_name_1_adapter)
        self.random_play_agent_2.init_with_adapter(self.ctx.random_play_config.agent_name_2_adapter)