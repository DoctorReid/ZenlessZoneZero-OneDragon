from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import FluentIcon

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.envs.env_config import env_config, RepositoryTypeEnum
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard


class SettingEnvInterface(VerticalScrollInterface):

    def __init__(self, parent=None):

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        self.repository_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.APPLICATION, title='代码源',
            options=[i.value for i in RepositoryTypeEnum]
        )
        self.repository_type_opt.value_changed.connect(self.on_repo_type_changed)

        content_layout.addWidget(self.repository_type_opt)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        VerticalScrollInterface.__init__(self, object_name='setting_env_interface',
                                         content_widget=content_widget, parent=parent,
                                         nav_text_cn='脚本环境')

        self.env_config = env_config

    def init_on_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        repo_type = get_config_item_from_enum(RepositoryTypeEnum, self.env_config.repository_type)
        self.repository_type_opt.setValue(repo_type.value)

    def on_repo_type_changed(self, index: int, value: str) -> None:
        """
        仓库类型改变
        :param index: 选项下标
        :param value: 值
        :return:
        """
        print(value)
        config_item = get_config_item_from_enum(RepositoryTypeEnum, value)
        self.env_config.repository_type = config_item.value
