import os
import shutil
import hashlib
import ctypes
from ctypes import wintypes

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget, QFileDialog
from qfluentwidgets import FluentIcon, SettingCardGroup, setTheme, Theme, VBoxLayout, PrimaryPushButton, PasswordLineEdit, MessageBox

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.base.operation.one_dragon_custom_context import OneDragonCustomContext
from one_dragon.custom.custom_config import ThemeEnum
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt


class SettingCustomInterface(VerticalScrollInterface):

    def __init__(self, ctx: OneDragonCustomContext, parent=None):
        self.ctx: OneDragonCustomContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='setting_custom_interface',
            content_widget=None, parent=parent,
            nav_text_cn='自定义设置'
        )

    def get_content_widget(self) -> QWidget:
        content_widget = QWidget()
        content_layout = VBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        content_layout.addWidget(self._init_basic_group())

        return content_widget

    def _init_basic_group(self) -> SettingCardGroup:
        basic_group = SettingCardGroup(gt('外观', 'ui'))

        self.theme_opt = ComboBoxSettingCard(
            icon=FluentIcon.CONSTRACT, title='界面主题',
            options_enum=ThemeEnum
        )
        self.theme_opt.value_changed.connect(self._on_theme_changed)
        basic_group.addSettingCard(self.theme_opt)

        self.banner_opt = SwitchSettingCard(icon=FluentIcon.PHOTO, title='自定义主页背景', content='设置后重启脚本生效')
        self.banner_opt.value_changed.connect(self._on_banner_changed)
        self.banner_select_btn = PrimaryPushButton(FluentIcon.EDIT, '选择', self)
        self.banner_select_btn.clicked.connect(self._on_banner_select_clicked)
        self.banner_opt.hBoxLayout.addWidget(self.banner_select_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.banner_password = PasswordLineEdit()
        self.banner_password.setPlaceholderText('使用此功能需要密码哦~')
        self.banner_password.setMinimumWidth(210)
        self.banner_opt.hBoxLayout.insertWidget(4, self.banner_password, 0, Qt.AlignmentFlag.AlignRight)
        self.banner_opt.hBoxLayout.addSpacing(16)
        basic_group.addSettingCard(self.banner_opt)

        return basic_group


    def on_interface_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        VerticalScrollInterface.on_interface_shown(self)
        theme = get_config_item_from_enum(ThemeEnum, self.ctx.custom_config.theme)
        if theme is not None:
            self.theme_opt.setValue(theme.value)
        
        self.banner_opt.init_with_adapter(self.ctx.custom_config.get_prop_adapter('banner'))
        if not self.ctx.custom_config.banner:
            self.banner_select_btn.setEnabled(False)


    def _on_theme_changed(self, index: int, value: str) -> None:
        """
        仓库类型改变
        :param index: 选项下标
        :param value: 值
        :return:
        """
        config_item = get_config_item_from_enum(ThemeEnum, value)
        self.ctx.custom_config.theme = config_item.value
        setTheme(Theme[config_item.value.upper()],lazy=True)

    def _on_banner_changed(self, value: bool) -> None:
        if value:
            correct_password_hash = 'd7103a21d03b8b922c3af3d477a0adde1633053cde1a7574e8009293ca3b70f1'
            def _hash_password(password: str) -> str:
                return hashlib.sha256(password.encode()).hexdigest()
            if _hash_password(self.banner_password.text()) != correct_password_hash:
                MessageBox('嘻嘻~', '密码不对哦~', self).exec()
                self.banner_opt.setValue(False)
                self.banner_select_btn.setEnabled(False)
            else:
                self.banner_select_btn.setEnabled(True)
        else:
            self.banner_select_btn.setEnabled(False)

    def _on_banner_select_clicked(self) -> None:
        """
        选择背景图片并复制
        """
        # 将默认路径设为图片库路径
        default_path = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 0x0027, None, 0, default_path)
        file_path, _ = QFileDialog.getOpenFileName(self, gt('选择你的背景图片'), default_path.value, filter="Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if file_path is not None and file_path != '':
            banner_path = os.path.join(
            os_utils.get_path_under_work_dir('custom', 'assets', 'ui'),
            'banner')
            shutil.copyfile(file_path, banner_path)
