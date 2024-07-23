from PySide6.QtCore import Signal

from one_dragon.gui.component.setting_card.multi_push_setting_card import MultiPushSettingCard


class AppRunCard(MultiPushSettingCard):

    MOVE_UP = Signal(str)
    RUN = Signal(str)

    def __init__(self, app_id: str, app_name: str):
        pass