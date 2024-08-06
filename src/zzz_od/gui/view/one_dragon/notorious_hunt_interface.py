from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, ComboBox, CaptionLabel, LineEdit
from typing import Optional

from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.multi_push_setting_card import MultiPushSettingCard
from zzz_od.application.battle_assistant.auto_battle_config import get_auto_battle_op_config_list
from zzz_od.application.charge_plan.charge_plan_config import ChargePlanItem
from zzz_od.context.zzz_context import ZContext


class ChargePlanCard(MultiPushSettingCard):

    changed = Signal(int, ChargePlanItem)

    def __init__(self, ctx: ZContext,
                 idx: int, plan: ChargePlanItem):
        self.ctx: ZContext = ctx
        self.idx: int = idx
        self.plan: ChargePlanItem = plan

        self.mission_type_combo_box = ComboBox()
        self.mission_type_combo_box.setDisabled(True)
        self._init_mission_type_combo_box()

        self.auto_battle_combo_box = ComboBox()
        self._init_auto_battle_box()

        run_times_label = CaptionLabel(text='已运行次数')
        self.run_times_input = LineEdit()
        self.run_times_input.setText(str(self.plan.run_times))
        self.run_times_input.textChanged.connect(self._on_run_times_changed)

        plan_times_label = CaptionLabel(text='计划次数')
        self.plan_times_input = LineEdit()
        self.plan_times_input.setText(str(self.plan.plan_times))
        self.plan_times_input.textChanged.connect(self._on_plan_times_changed)

        MultiPushSettingCard.__init__(
            self,
            icon=FluentIcon.CALENDAR,
            title='',
            btn_list=[
                self.mission_type_combo_box,
                self.auto_battle_combo_box,
                run_times_label,
                self.run_times_input,
                plan_times_label,
                self.plan_times_input,
            ]
        )

    def _init_mission_type_combo_box(self) -> None:
        try:
            self.mission_type_combo_box.currentIndexChanged.disconnect(self._on_mission_type_changed)
        except Exception:
            pass

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

        self.mission_type_combo_box.currentIndexChanged.connect(self._on_mission_type_changed)

    def _init_auto_battle_box(self) -> None:
        try:
            self.auto_battle_combo_box.currentIndexChanged.disconnect(self._on_auto_battle_changed)
        except Exception:
            pass

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

        self.auto_battle_combo_box.currentIndexChanged.connect(self._on_auto_battle_changed)

    def _on_mission_type_changed(self, idx: int) -> None:
        mission_type_name = self.mission_type_combo_box.itemData(idx)
        self.plan.mission_type_name = mission_type_name

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
            ctx=ctx,
            object_name='zzz_notorious_hunt_plan_interface',
            content_widget=None, parent=parent,
            nav_text_cn='恶名狩猎计划'
        )

    def get_content_widget(self) -> QWidget:
        self.content_widget = ColumnWidget()

        return self.content_widget

    def update_plan_list_display(self):
        self.content_widget.clear_widgets()

        for idx, plan_item in enumerate(self.ctx.notorious_hunt_config.plan_list):
            card = ChargePlanCard(self.ctx, idx, plan_item)
            card.changed.connect(self._on_plan_item_changed)
            self.content_widget.add_widget(card)

        self.content_widget.add_stretch(1)

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)
        self.update_plan_list_display()

    def on_interface_hidden(self) -> None:
        VerticalScrollInterface.on_interface_hidden(self)

    def _on_plan_item_changed(self, idx: int, plan: ChargePlanItem) -> None:
        self.ctx.notorious_hunt_config.update_plan(idx, plan)
