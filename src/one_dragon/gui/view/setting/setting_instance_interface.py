from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, SettingCardGroup, setTheme, Theme, VBoxLayout

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.envs.env_config import RepositoryTypeEnum, GitMethodEnum, ProxyTypeEnum, ThemeEnum
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.key_setting_card import KeySettingCard
from one_dragon.gui.component.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.utils.i18_utils import gt


class SettingInstanceInterface(VerticalScrollInterface):

    def __init__(self, ctx: OneDragonContext, parent=None):
        self.ctx: OneDragonContext = ctx

        VerticalScrollInterface.__init__(
            self,
            ctx=ctx,
            object_name='setting_instance_interface',
            content_widget=None, parent=parent,
            nav_text_cn='实例设置'
        )

    def get_content_widget(self) -> QWidget:
        """
        子界面内的内容组件 由子类实现
        :return:
        """
        self.content_widget = ColumnWidget()
        return self.content_widget

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.content_widget.clear_widgets()

        for instance in self.ctx.one_dragon_config.instance_list:
            group = SettingCardGroup('%s-%02d' % (gt('实例', 'ui'), instance.idx))
