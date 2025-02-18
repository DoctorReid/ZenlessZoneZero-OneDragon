from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import PrimaryPushButton, FluentIcon, CaptionLabel, LineEdit, ToolButton
from typing import List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon_qt.widgets.column import Column
from one_dragon_qt.widgets.combo_box import ComboBox
from one_dragon_qt.widgets.setting_card.multi_push_setting_card import MultiLineSettingCard
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from zzz_od.application.battle_assistant.auto_battle_config import get_auto_battle_op_config_list
from zzz_od.application.charge_plan.charge_plan_config import ChargePlanItem, CardNumEnum
from zzz_od.application.notorious_hunt.notorious_hunt_config import NotoriousHuntBuffEnum
from zzz_od.context.zzz_context import ZContext


class ChargePlanCard(MultiLineSettingCard):

    changed = Signal(int, ChargePlanItem)
    delete = Signal(int)
    move_up = Signal(int)

    def __init__(self, ctx: ZContext,
                 idx: int, plan: ChargePlanItem):
        self.ctx: ZContext = ctx
        self.idx: int = idx
        self.plan: ChargePlanItem = plan

        self.category_combo_box = ComboBox()
        self.category_combo_box.currentIndexChanged.connect(self._on_category_changed)

        self.mission_type_combo_box = ComboBox()
        self.mission_type_combo_box.currentIndexChanged.connect(self._on_mission_type_changed)

        self.mission_combo_box = ComboBox()
        self.mission_combo_box.currentIndexChanged.connect(self._on_mission_changed)

        self.card_num_box = ComboBox()
        self.card_num_box.currentIndexChanged.connect(self._on_card_num_changed)

        self.notorious_hunt_buff_num_opt = ComboBox()
        self.notorious_hunt_buff_num_opt.currentIndexChanged.connect(self.on_notorious_hunt_buff_num_changed)

        self.predefined_team_opt = ComboBox()
        self.predefined_team_opt.currentIndexChanged.connect(self.on_predefined_team_changed)

        self.auto_battle_combo_box = ComboBox()
        self.auto_battle_combo_box.currentIndexChanged.connect(self._on_auto_battle_changed)

        run_times_label = CaptionLabel(text='已运行次数')
        self.run_times_input = LineEdit()
        self.run_times_input.textChanged.connect(self._on_run_times_changed)

        plan_times_label = CaptionLabel(text='计划次数')
        self.plan_times_input = LineEdit()
        self.plan_times_input.textChanged.connect(self._on_plan_times_changed)

        self.move_up_btn = ToolButton(FluentIcon.UP, None)
        self.move_up_btn.clicked.connect(self._on_move_up_clicked)
        self.del_btn = ToolButton(FluentIcon.DELETE, None)
        self.del_btn.clicked.connect(self._on_del_clicked)

        MultiLineSettingCard.__init__(
            self,
            icon=FluentIcon.CALENDAR,
            title='',
            line_list=[
                [
                    self.category_combo_box,
                    self.mission_type_combo_box,
                    self.mission_combo_box,
                    self.card_num_box,
                    self.notorious_hunt_buff_num_opt,
                    self.predefined_team_opt,
                    self.auto_battle_combo_box,
                ],
                [
                    run_times_label,
                    self.run_times_input,
                    plan_times_label,
                    self.plan_times_input,
                    self.move_up_btn,
                    self.del_btn,
                ]
            ]
        )

        self.init_with_plan(plan)

    def init_category_combo_box(self) -> None:
        config_list = self.ctx.compendium_service.get_charge_plan_category_list()
        self.category_combo_box.set_items(config_list, self.plan.category_name)

    def init_mission_type_combo_box(self) -> None:
        config_list = self.ctx.compendium_service.get_charge_plan_mission_type_list(self.plan.category_name)
        self.mission_type_combo_box.set_items(config_list, self.plan.mission_type_name)

    def init_mission_combo_box(self) -> None:
        config_list = self.ctx.compendium_service.get_charge_plan_mission_list(self.plan.category_name, self.plan.mission_type_name)
        self.mission_combo_box.set_items(config_list, self.plan.mission_name)
        self.mission_combo_box.setVisible(self.plan.category_name == '实战模拟室')

    def init_card_num_box(self) -> None:
        config_list = [config_enum.value for config_enum in CardNumEnum]
        self.card_num_box.set_items(config_list, self.plan.card_num)
        self.card_num_box.setVisible(self.plan.category_name == '实战模拟室')

    def init_notorious_hunt_buff_num_opt(self) -> None:
        """
        初始化不透明度下拉框
        """
        config_list = [config_enum.value for config_enum in NotoriousHuntBuffEnum]
        self.notorious_hunt_buff_num_opt.set_items(config_list, self.plan.notorious_hunt_buff_num)
        self.notorious_hunt_buff_num_opt.setVisible(self.plan.category_name == '恶名狩猎')

    def init_predefined_team_opt(self) -> None:
        """
        初始化预备编队的下拉框
        """
        config_list = ([ConfigItem('游戏内配队', -1)] +
                       [ConfigItem(team.name, team.idx) for team in self.ctx.team_config.team_list])
        self.predefined_team_opt.set_items(config_list, self.plan.predefined_team_idx)

    def init_auto_battle_box(self) -> None:
        config_list = get_auto_battle_op_config_list(sub_dir='auto_battle')
        self.auto_battle_combo_box.set_items(config_list, self.plan.auto_battle_config)
        self.auto_battle_combo_box.setVisible(self.plan.predefined_team_idx == -1)

    def init_run_times_input(self) -> None:
        self.run_times_input.blockSignals(True)
        self.run_times_input.setText(str(self.plan.run_times))
        self.run_times_input.blockSignals(False)

    def init_plan_times_input(self) -> None:
        self.plan_times_input.blockSignals(True)
        self.plan_times_input.setText(str(self.plan.plan_times))
        self.plan_times_input.blockSignals(False)

    def init_with_plan(self, plan: ChargePlanItem) -> None:
        """
        以一个体力计划进行初始化
        """
        self.plan = plan

        self.init_category_combo_box()
        self.init_mission_type_combo_box()
        self.init_mission_combo_box()

        self.init_card_num_box()
        self.init_notorious_hunt_buff_num_opt()
        self.init_predefined_team_opt()
        self.init_auto_battle_box()

        self.init_run_times_input()
        self.init_plan_times_input()

    def _on_category_changed(self, idx: int) -> None:
        category_name = self.category_combo_box.itemData(idx)
        self.plan.category_name = category_name

        self.init_mission_type_combo_box()
        self.init_mission_combo_box()
        self.init_card_num_box()
        self.init_notorious_hunt_buff_num_opt()

        self.update_by_history()

        self._emit_value()

    def _on_mission_type_changed(self, idx: int) -> None:
        mission_type_name = self.mission_type_combo_box.itemData(idx)
        self.plan.mission_type_name = mission_type_name

        self.init_mission_combo_box()

        self.update_by_history()
        self._emit_value()

    def _on_mission_changed(self, idx: int) -> None:
        mission_name = self.mission_combo_box.itemData(idx)
        self.plan.mission_name = mission_name

        self.update_by_history()
        self._emit_value()

    def _on_card_num_changed(self, idx: int) -> None:
        self.plan.card_num = self.card_num_box.itemData(idx)
        self._emit_value()

    def on_notorious_hunt_buff_num_changed(self, idx: int) -> None:
        self.plan.notorious_hunt_buff_num = self.notorious_hunt_buff_num_opt.currentData()
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

    def _on_move_up_clicked(self) -> None:
        self.move_up.emit(self.idx)

    def _on_del_clicked(self) -> None:
        self.delete.emit(self.idx)

    def update_by_history(self) -> None:
        """
        根据历史记录更新
        """
        history = self.ctx.charge_plan_config.get_history_by_uid(self.plan)
        if history is None:
            return

        self.plan.card_num = history.card_num
        self.plan.notorious_hunt_buff_num = history.notorious_hunt_buff_num
        self.plan.predefined_team_idx = history.predefined_team_idx
        self.plan.auto_battle_config = history.auto_battle_config
        self.plan.plan_times = history.plan_times

        self.init_card_num_box()
        self.init_notorious_hunt_buff_num_opt()
        self.init_predefined_team_opt()
        self.init_auto_battle_box()
        self.init_plan_times_input()


class ChargePlanInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='zzz_charge_plan_interface',
            content_widget=None, parent=parent,
            nav_text_cn='体力计划'
        )

    def get_content_widget(self) -> QWidget:
        self.content_widget = Column()

        self.loop_opt = SwitchSettingCard(icon=FluentIcon.SYNC, title='循环执行', content='开启时 会循环执行到体力用尽')
        self.loop_opt.setValue(self.ctx.charge_plan_config.loop)
        self.loop_opt.value_changed.connect(self._on_loop_changed)
        self.content_widget.add_widget(self.loop_opt)

        self.card_list: List[ChargePlanCard] = []

        self.plus_btn = PrimaryPushButton(text='新增')
        self.plus_btn.clicked.connect(self._on_add_clicked)
        self.content_widget.add_widget(self.plus_btn)

        return self.content_widget

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)
        self.update_plan_list_display()

    def on_interface_hidden(self) -> None:
        VerticalScrollInterface.on_interface_hidden(self)

    def update_plan_list_display(self):
        plan_list = self.ctx.charge_plan_config.plan_list

        if len(plan_list) > len(self.card_list):
            self.content_widget.remove_widget(self.plus_btn)

            while len(self.card_list) < len(plan_list):
                idx = len(self.card_list)
                card = ChargePlanCard(self.ctx, idx, self.ctx.charge_plan_config.plan_list[idx])
                card.changed.connect(self._on_plan_item_changed)
                card.delete.connect(self._on_plan_item_deleted)
                card.move_up.connect(self._on_plan_item_move_up)

                self.card_list.append(card)
                self.content_widget.add_widget(card)

            self.content_widget.add_widget(self.plus_btn, stretch=1)

        for idx, plan in enumerate(plan_list):
            card = self.card_list[idx]
            card.init_with_plan(plan)

        while len(self.card_list) > len(plan_list):
            card = self.card_list[-1]
            self.content_widget.remove_widget(card)
            card.deleteLater()
            self.card_list.pop(-1)

    def _on_add_clicked(self) -> None:
        self.ctx.charge_plan_config.add_plan()
        self.update_plan_list_display()

    def _on_plan_item_changed(self, idx: int, plan: ChargePlanItem) -> None:
        self.ctx.charge_plan_config.update_plan(idx, plan)

    def _on_plan_item_deleted(self, idx: int) -> None:
        self.ctx.charge_plan_config.delete_plan(idx)
        self.update_plan_list_display()

    def _on_plan_item_move_up(self, idx: int) -> None:
        self.ctx.charge_plan_config.move_up(idx)
        self.update_plan_list_display()

    def _on_loop_changed(self, new_value: bool) -> None:
        self.ctx.charge_plan_config.loop = new_value