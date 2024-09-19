import time

from PySide6.QtCore import QTimer
from PySide6.QtGui import QBrush
from PySide6.QtWidgets import QTableWidgetItem
from qfluentwidgets import TableWidget, FluentThemeColor
from typing import Optional, List

from one_dragon.base.conditional_operation.state_recorder import StateRecord, StateRecorder
from one_dragon.utils.i18_utils import gt
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator


class BattleStateDisplay(TableWidget):

    def __init__(self, parent=None):
        TableWidget.__init__(self, parent=parent)

        self.auto_op: Optional[AutoBattleOperator] = None
        self.last_states: List[StateRecord] = []

        self.setBorderVisible(True)
        self.setBorderRadius(8)

        self.setWordWrap(True)
        self.setColumnCount(3)
        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 50)
        self.verticalHeader().hide()
        self.setHorizontalHeaderLabels([
            gt('状态', 'ui'),
            gt('触发秒数', 'ui'),
            gt('状态值', 'ui'),
        ])

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)

    def set_update_display(self, to_update: bool) -> None:
        if to_update:
            self.update_timer.stop()
            self.update_timer.start(100)
        else:
            self.update_timer.stop()

    def _update_display(self) -> None:
        if self.auto_op is None or not self.auto_op.is_running:
            self.setRowCount(0)
            return

        states = self.auto_op.get_usage_states()
        states = sorted(states)

        state_recorders: List[StateRecorder] = sorted([i for i in self.auto_op.state_recorders.values()],
                                                      key=lambda x: x.state_name)

        now = time.time()
        new_states = []
        for recorder in state_recorders:
            if recorder.last_record_time == -1:
                continue
            new_states.append(StateRecord(recorder.state_name, recorder.last_record_time, recorder.last_value))

        total = len(new_states)
        self.setRowCount(total)
        for i in range(total):
            state_item = QTableWidgetItem(new_states[i].state_name)
            if i >= len(self.last_states) or new_states[i].state_name != self.last_states[i].state_name:
                state_item.setBackground(QBrush(FluentThemeColor.RED.value))

            time_diff = now - new_states[i].trigger_time
            if time_diff > 999:
                time_diff = 999
            time_item = QTableWidgetItem('%.4f' % time_diff)
            if i >= len(self.last_states) or new_states[i].trigger_time != self.last_states[i].trigger_time:
                time_item.setBackground(QBrush(FluentThemeColor.RED.value))

            value_item = QTableWidgetItem(str(new_states[i].value) if new_states[i].value is not None else '')
            if i >= len(self.last_states) or new_states[i].value != self.last_states[i].value:
                value_item.setBackground(QBrush(FluentThemeColor.RED.value))

            self.setItem(i, 0, state_item)
            self.setItem(i, 1, time_item)
            self.setItem(i, 2, value_item)

        self.last_states = new_states
