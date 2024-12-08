from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, LineEdit, HyperlinkCard
from typing import Optional, List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.gui.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.widgets.setting_card.multi_push_setting_card import MultiPushSettingCard
from zzz_od.application.battle_assistant.auto_battle_config import get_auto_battle_op_config_list
from zzz_od.config.team_config import PredefinedTeamInfo
from zzz_od.context.zzz_context import ZContext

from phosdeiz.gui.widgets import Column,ComboBox

class TeamSettingCard(MultiPushSettingCard):

    changed = Signal(PredefinedTeamInfo)

    def __init__(self):
        self.team_info: Optional[PredefinedTeamInfo] = None

        self.name_input = LineEdit()
        self.name_input.textChanged.connect(self.on_name_changed)

        self.auto_battle_btn = ComboBox()
        self.auto_battle_btn.currentIndexChanged.connect(self.on_auto_battle_changed)

        MultiPushSettingCard.__init__(self, icon=FluentIcon.PEOPLE, title='预备编队',
                                      btn_list=[self.name_input, self.auto_battle_btn])

    def init_auto_battle_btn(self, auto_battle_list: List[ConfigItem]) -> None:
        """
        初始化自动战斗配置的下拉框
        """
        self.auto_battle_btn.blockSignals(True)

        self.auto_battle_btn.clear()
        for config in auto_battle_list:
            self.auto_battle_btn.addItem(text=config.label, userData=config.value)

        self.auto_battle_btn.blockSignals(False)

    def init_with_team(self, team: PredefinedTeamInfo) -> None:
        self.team_info = team

        self.name_input.blockSignals(True)
        self.name_input.setText(self.team_info.name)
        self.name_input.blockSignals(False)

        self.auto_battle_btn.blockSignals(True)
        for idx, item in enumerate(self.auto_battle_btn.items):
            if item.userData == team.auto_battle:
                self.auto_battle_btn.setCurrentIndex(idx)
                break
        self.auto_battle_btn.blockSignals(False)

    def on_name_changed(self, value: str) -> None:
        if self.team_info is None:
            return

        self.team_info.name = value
        self.changed.emit(self.team_info)

    def on_auto_battle_changed(self, idx: int) -> None:
        if self.team_info is None:
            return

        self.team_info.auto_battle = self.auto_battle_btn.itemData(idx)
        self.changed.emit(self.team_info)


class SettingTeamInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='setting_team_interface',
            content_widget=None, parent=parent,
            nav_text_cn='预备编队'
        )
        self.ctx: ZContext = ctx

    def get_content_widget(self) -> QWidget:
        content_widget = Column()

        self.help_opt = HyperlinkCard(icon=FluentIcon.HELP, title='使用默认队伍名称出现错选时 可更改名字解决',
                                      text='', url='')
        content_widget.add_widget(self.help_opt)

        self.team_opt_list = []
        team_list = self.ctx.team_config.team_list
        for _ in team_list:
            card = TeamSettingCard()
            card.changed.connect(self.on_team_info_changed)
            self.team_opt_list.append(card)
            content_widget.add_widget(card)

        content_widget.add_stretch(1)

        return content_widget

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        auto_battle_list = get_auto_battle_op_config_list('auto_battle')

        team_list = self.ctx.team_config.team_list
        for i in range(len(team_list)):
            if i >= len(self.team_opt_list):
                break

            self.team_opt_list[i].init_auto_battle_btn(auto_battle_list)
            self.team_opt_list[i].init_with_team(team_list[i])

    def on_team_info_changed(self, team: PredefinedTeamInfo) -> None:
        self.ctx.team_config.update_team(team)