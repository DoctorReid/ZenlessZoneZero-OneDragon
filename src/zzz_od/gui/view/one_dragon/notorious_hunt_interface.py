from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, ComboBox, CaptionLabel, LineEdit
from typing import Optional, List

from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.multi_push_setting_card import MultiPushSettingCard, MultiLineSettingCard
from one_dragon.utils.i18_utils import gt
from zzz_od.application.battle_assistant.auto_battle_config import get_auto_battle_op_config_list
from zzz_od.application.charge_plan.charge_plan_config import ChargePlanItem
from zzz_od.application.notorious_hunt.notorious_hunt_config import NotoriousHuntLevelEnum
from zzz_od.context.zzz_context import ZContext


class ChargePlanCard(MultiLineSettingCard):

    changed = Signal(int, ChargePlanItem)

    def __init__(self, ctx: ZContext,
                 idx: int, plan: ChargePlanItem):
        self.ctx: ZContext = ctx
        self.idx: int = idx
        self.plan: ChargePlanItem = plan

        self.mission_type_combo_box = ComboBox()
        self.mission_type_combo_box.setDisabled(True)
        self.mission_type_combo_box.currentIndexChanged.connect(self._on_mission_type_changed)
        self.init_mission_type_combo_box()

        self.level_combo_box = ComboBox()
        self.level_combo_box.currentIndexChanged.connect(self._on_level_changed)
        self.init_level_combo_box()

        self.predefined_team_opt = ComboBox()
        self.predefined_team_opt.currentIndexChanged.connect(self.on_predefined_team_changed)

        self.auto_battle_combo_box = ComboBox()
        self.auto_battle_combo_box.currentIndexChanged.connect(self._on_auto_battle_changed)
        self.init_auto_battle_box()

        run_times_label = CaptionLabel(text='已运行次数')
        self.run_times_input = LineEdit()
        self.run_times_input.setText(str(self.plan.run_times))
        self.run_times_input.textChanged.connect(self._on_run_times_changed)

        plan_times_label = CaptionLabel(text='计划次数')
        self.plan_times_input = LineEdit()
        self.plan_times_input.setText(str(self.plan.plan_times))
        self.plan_times_input.textChanged.connect(self._on_plan_times_changed)

        MultiLineSettingCard.__init__(
            self,
            icon=FluentIcon.CALENDAR,
            title='',
            line_list=[
                [
                    self.mission_type_combo_box,
                    self.level_combo_box,
                    self.predefined_team_opt,
                    self.auto_battle_combo_box,
                ],
                [
                    run_times_label,
                    self.run_times_input,
                    plan_times_label,
                    self.plan_times_input,
                ]
            ]
        )

    def init_with_plan(self, plan: ChargePlanItem) -> None:
        """
        以一个体力计划进行初始化
        """
        self.plan = plan

        self.init_mission_type_combo_box()
        self.init_predefined_team_opt()
        self.init_auto_battle_box()

        self.run_times_input.blockSignals(True)
        self.run_times_input.setText(str(self.plan.run_times))
        self.run_times_input.blockSignals(False)

        self.plan_times_input.blockSignals(True)
        self.plan_times_input.setText(str(self.plan.plan_times))
        self.plan_times_input.blockSignals(False)

    def init_mission_type_combo_box(self) -> None:
        self.mission_type_combo_box.blockSignals(True)

        config_list = self.ctx.compendium_service.get_notorious_hunt_plan_mission_type_list(self.plan.category_name)
        self.mission_type_combo_box.clear()

        target_text: Optional[str] = None
        for config in config_list:
            self.mission_type_combo_box.addItem(text=config.ui_text, userData=config.value)
            if config.value == self.plan.mission_type_name:
                target_text = config.ui_text

        if target_text is None:
            self.mission_type_combo_box.setCurrentIndex(0)
            self.plan.mission_type_name = self.mission_type_combo_box.itemData(0)
        else:
            self.mission_type_combo_box.setText(target_text)

        self.mission_type_combo_box.blockSignals(False)

    def init_level_combo_box(self) -> None:
        self.level_combo_box.blockSignals(True)

        self.level_combo_box.clear()

        target_text: Optional[str] = None
        for i in NotoriousHuntLevelEnum:
            config = i.value
            self.level_combo_box.addItem(text=config.ui_text, userData=config.value)
            if config.value == self.plan.mission_type_name:
                target_text = config.ui_text

        if target_text is None:
            self.level_combo_box.setCurrentIndex(0)
            self.plan.level = self.level_combo_box.itemData(0)
        else:
            self.level_combo_box.setText(target_text)

        self.level_combo_box.blockSignals(False)

    def init_auto_battle_box(self) -> None:
        self.auto_battle_combo_box.setVisible(self.plan.predefined_team_idx == -1)
        self.auto_battle_combo_box.blockSignals(True)

        config_list = get_auto_battle_op_config_list(sub_dir='auto_battle')
        self.auto_battle_combo_box.clear()

        target_text: Optional[str] = None
        for config in config_list:
            self.auto_battle_combo_box.addItem(text=config.ui_text, userData=config.value)
            if config.value == self.plan.auto_battle_config:
                target_text = config.ui_text

        if target_text is None:
            self.auto_battle_combo_box.setCurrentIndex(0)
            self.plan.auto_battle_config = self.auto_battle_combo_box.itemData(0)
        else:
            self.auto_battle_combo_box.setText(target_text)

        self.auto_battle_combo_box.blockSignals(False)

    def init_predefined_team_opt(self) -> None:
        """
        初始化预备编队的下拉框
        """
        self.predefined_team_opt.blockSignals(True)

        self.predefined_team_opt.clear()
        self.predefined_team_opt.addItem(text=gt('游戏内配队'), userData=-1)

        for team in self.ctx.team_config.team_list:
            self.predefined_team_opt.addItem(text=team.name, userData=team.idx)

        self.predefined_team_opt.setCurrentIndex(self.plan.predefined_team_idx + 1)

        self.predefined_team_opt.blockSignals(False)

    def _on_mission_type_changed(self, idx: int) -> None:
        mission_type_name = self.mission_type_combo_box.itemData(idx)
        self.plan.mission_type_name = mission_type_name

        self._emit_value()

    def _on_level_changed(self, idx: int) -> None:
        level = self.level_combo_box.itemData(idx)
        self.plan.level = level

        self._emit_value()

    def on_predefined_team_changed(self, idx: int) -> None:
        self.plan.predefined_team_idx = self.predefined_team_opt.currentData()
        self.init_auto_battle_box()
        self._emit_value()

    def _on_auto_battle_changed(self, idx: int) -> None:
        auto_battle = self.auto_battle_combo_box.itemData(idx)
        self.plan.auto_battle_config = auto_battle

        self._emit_value()

    def _on_run_times_changed(self) -> None:
        self.plan.run_times = int(self.run_times_input.text())
        self._emit_value()

    def _on_plan_times_changed(self) -> None:
        self.plan.plan_times = int(self.plan_times_input.text())
        self._emit_value()

    def _emit_value(self) -> None:
        self.changed.emit(self.idx, self.plan)


class NotoriousHuntPlanInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='zzz_notorious_hunt_plan_interface',
            content_widget=None, parent=parent,
            nav_text_cn='恶名狩猎计划'
        )

    def get_content_widget(self) -> QWidget:
        self.content_widget = ColumnWidget()

        self.card_list: List[ChargePlanCard] = []

        return self.content_widget

    def update_plan_list_display(self):
        plan_list = self.ctx.notorious_hunt_config.plan_list

        if len(plan_list) > len(self.card_list):
            while len(self.card_list) < len(plan_list):
                idx = len(self.card_list)
                card = ChargePlanCard(self.ctx, idx, self.ctx.charge_plan_config.plan_list[idx])
                card.changed.connect(self._on_plan_item_changed)

                self.card_list.append(card)
                self.content_widget.add_widget(card)

        for idx, plan in enumerate(plan_list):
            card = self.card_list[idx]
            card.init_with_plan(plan)

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)
        self.update_plan_list_display()

    def on_interface_hidden(self) -> None:
        VerticalScrollInterface.on_interface_hidden(self)

    def _on_plan_item_changed(self, idx: int, plan: ChargePlanItem) -> None:
        self.ctx.notorious_hunt_config.update_plan(idx, plan)
