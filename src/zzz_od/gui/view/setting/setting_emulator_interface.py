import os
from PySide6.QtWidgets import QWidget, QFileDialog
from qfluentwidgets import SettingCardGroup, FluentIcon, PushSettingCard

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.base.controller.pc_button.ds4_button_controller import Ds4ButtonEnum
from one_dragon.base.controller.pc_button.xbox_button_controller import XboxButtonEnum
from one_dragon.gui.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.widgets.setting_card.key_setting_card import KeySettingCard
from one_dragon.gui.widgets.setting_card.text_setting_card import TextSettingCard
from one_dragon.gui.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from phosdeiz.gui.widgets import Column
from zzz_od.config.game_config import GamePlatformEnum, GameRegionEnum, GamepadTypeEnum, TypeInputWay
from zzz_od.config.emulator_config import GameClient
from zzz_od.context.zzz_context import ZContext

class SettingEmulatorInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='setting_emulator_interface',
            content_widget=None, parent=parent,
            nav_text_cn='模拟器设置'
        )
        self.ctx: ZContext = ctx

    def get_content_widget(self) -> QWidget:
        content_widget = Column()

        content_widget.add_widget(self._get_basic_group())
        # content_widget.add_widget(self._get_key_group())
        # content_widget.add_widget(self._get_gamepad_group())
        content_widget.add_stretch(1)

        return content_widget

    def _get_basic_group(self) -> QWidget:
        basic_group = SettingCardGroup(gt('模拟器基础', 'ui'))

        self.game_client_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='游戏客户端', options_enum=GameClient)
        basic_group.addSettingCard(self.game_client_opt)

        self.emulator_path_opt = PushSettingCard(icon=FluentIcon.FOLDER, title='模拟器路径', text='选择')
        self.emulator_path_opt.clicked.connect(self._on_emulator_path_clicked)
        basic_group.addSettingCard(self.emulator_path_opt)

        self.emulator_serial_opt = TextSettingCard(icon=FluentIcon.PEOPLE, title='模拟器 Serial')
        basic_group.addSettingCard(self.emulator_serial_opt)

        return basic_group

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        # 初始化模拟器相关配置
        self.game_client_opt.init_with_adapter(self.ctx.emulator_config.get_prop_adapter('Alas.Emulator.GameClient'))
        self.emulator_path_opt.setContent(self.ctx.emulator_config.emulator_path)
        self.emulator_serial_opt.init_with_adapter(self.ctx.emulator_config.get_prop_adapter('Alas.Emulator.Serial'))

    def _on_emulator_path_clicked(self) -> None:
        """
        当点击模拟器路径选择按钮时，弹出文件选择对话框
        """
        file_path, _ = QFileDialog.getOpenFileName(self, gt('选择模拟器可执行文件'), filter="Exe (*.exe)")
        if file_path is not None and file_path.endswith('.exe'):
            log.info('选择模拟器路径 %s', file_path)
            self._on_emulator_path_chosen(os.path.normpath(file_path))

    def _on_emulator_path_chosen(self, file_path) -> None:
        """
        当模拟器路径选择完成后，更新配置并显示在界面上
        """
        self.ctx.emulator_config.emulator_path = file_path
        self.emulator_path_opt.setContent(file_path)