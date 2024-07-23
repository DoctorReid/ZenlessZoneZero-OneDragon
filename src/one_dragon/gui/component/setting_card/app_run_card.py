from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon
from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord
from one_dragon.gui.component.setting_card.multi_push_setting_card import MultiPushSettingCard
from one_dragon.utils.i18_utils import gt


class AppRunCard(MultiPushSettingCard):

    MOVE_UP = Signal(str)
    RUN = Signal(str)

    def __init__(self, app_id: str, app_name: str, app_run_record: AppRunRecord, parent: Optional[QWidget] = None):
        MultiPushSettingCard.__init__(
            self,
            btn_list=[],
            icon=FluentIcon.GAME,
            title=gt(app_name, 'ui'),
            parent=parent,
        )

        self.app_id: str = app_id
        self.run_record: AppRunRecord = app_run_record

    def update_display(self) -> None:
        pass