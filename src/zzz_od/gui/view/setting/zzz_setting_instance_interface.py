from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, ComboBox, LineEdit, PushButton, \
    ToolButton, PrimaryPushButton

from one_dragon.base.config.one_dragon_config import OneDragonInstance, RunInOneDragonApp
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.multi_push_setting_card import MultiPushSettingCard
from one_dragon.gui.view.setting.setting_instance_interface import SettingInstanceInterface
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


class ZSettingInstanceInterface(SettingInstanceInterface):

    def __init__(self, ctx: OneDragonContext, parent=None):
        self.ctx: OneDragonContext = ctx

        SettingInstanceInterface.__init__(
            self,
            ctx=ctx,
            parent=parent
        )