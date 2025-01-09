from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QWidget
from qfluentwidgets import SettingCardGroup, FluentIcon

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.gui.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.utils.i18_utils import gt
from phosdeiz.gui.widgets import Column
from zzz_od.application.drive_disc_dismantle.drive_disc_dismantle_config import DismantleLevelEnum
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import AgentEnum


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

        content_widget.add_widget(self.get_coffee_shop_group())
        content_widget.add_widget(self.get_drive_disc_dismantle_group())
        content_widget.add_stretch(1)

        return content_widget

    def get_coffee_shop_group(self) -> QWidget:
        group = SettingCardGroup(gt('影像店'))

        self.random_play_agent_1 = ComboBoxSettingCard(
            icon=FluentIcon.PEOPLE, title=gt('影像店代理人-1'),
            options_list=[ConfigItem(self.ctx.random_play_config.random_agent_name())] + [
                ConfigItem(agent_enum.value.agent_name)
                for agent_enum in AgentEnum
            ],
        )
        group.addSettingCard(self.random_play_agent_1)

        self.random_play_agent_2 = ComboBoxSettingCard(
            icon=FluentIcon.PEOPLE, title=gt('影像店代理人-2'),
            options_list=[ConfigItem(self.ctx.random_play_config.random_agent_name())] + [
                ConfigItem(agent_enum.value.agent_name)
                for agent_enum in AgentEnum
            ],
        )
        group.addSettingCard(self.random_play_agent_2)

        return group

    def get_drive_disc_dismantle_group(self) -> QWidget:
        group = SettingCardGroup(gt('驱动盘拆解'))

        self.drive_disc_dismantle_level_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='驱动盘拆解等级',
                                                           options_enum=DismantleLevelEnum)
        group.addSettingCard(self.drive_disc_dismantle_level_opt)

        self.drive_disc_dismantle_abandon_opt = SwitchSettingCard(icon=FluentIcon.GAME, title='全部已弃置')
        group.addSettingCard(self.drive_disc_dismantle_abandon_opt)

        return group

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.random_play_agent_1.init_with_adapter(self.ctx.random_play_config.get_prop_adapter('agent_name_1'))
        self.random_play_agent_2.init_with_adapter(self.ctx.random_play_config.get_prop_adapter('agent_name_2'))

        self.drive_disc_dismantle_level_opt.init_with_adapter(self.ctx.drive_disc_dismantle_config.get_prop_adapter('dismantle_level'))
        self.drive_disc_dismantle_abandon_opt.init_with_adapter(self.ctx.drive_disc_dismantle_config.get_prop_adapter('dismantle_abandon'))
