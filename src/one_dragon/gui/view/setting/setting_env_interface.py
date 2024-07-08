from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import FluentIcon, SettingCardGroup, setTheme, Theme, VBoxLayout

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.envs.env_config import env_config, RepositoryTypeEnum, GitMethodEnum, ProxyTypeEnum, ThemeEnum
from one_dragon.envs.git_service import git_service
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.utils.i18_utils import gt


class SettingEnvInterface(VerticalScrollInterface):

    def __init__(self, parent=None):

        content_widget = QWidget()
        content_layout = VBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        gui_group = SettingCardGroup(gt('界面相关', 'ui'))
        content_layout.addWidget(gui_group)

        self.theme_opt = ComboBoxSettingCard(
            icon=FluentIcon.CONSTRACT, title='主题', content='有没有大神提供个好配色',
            options=ThemeEnum
        )
        self.theme_opt.value_changed.connect(self._on_theme_changed)
        gui_group.addSettingCard(self.theme_opt)

        git_group = SettingCardGroup(gt('Git相关', 'ui'))
        content_layout.addWidget(git_group)

        self.repository_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.APPLICATION, title='代码源', content='国内无法访问Github则选择Gitee',
            options=RepositoryTypeEnum
        )
        self.repository_type_opt.value_changed.connect(self._on_repo_type_changed)
        git_group.addSettingCard(self.repository_type_opt)

        self.git_method_opt = ComboBoxSettingCard(
            icon=FluentIcon.SYNC, title='拉取方式', content='不懂什么是ssh就选https',
            options=GitMethodEnum
        )
        self.git_method_opt.value_changed.connect(self._on_git_method_changed)
        git_group.addSettingCard(self.git_method_opt)

        web_group = SettingCardGroup(gt('网络相关', 'ui'))
        content_layout.addWidget(web_group)

        self.proxy_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.GLOBE, title='网络代理', content='免费代理仅能加速工具和模型下载，无法加速代码同步',
            options=ProxyTypeEnum
        )
        self.proxy_type_opt.value_changed.connect(self._on_proxy_type_changed)
        web_group.addSettingCard(self.proxy_type_opt)

        self.personal_proxy_input = TextSettingCard(
            icon=FluentIcon.WIFI, title='个人代理', content='网络代理中选择 个人代理 后生效',
            input_placeholder='http://127.0.0.1:8080'
        )
        self.personal_proxy_input.value_changed.connect(self._on_personal_proxy_changed)
        web_group.addSettingCard(self.personal_proxy_input)

        VerticalScrollInterface.__init__(self, object_name='setting_env_interface',
                                         content_widget=content_widget, parent=parent,
                                         nav_text_cn='脚本环境')

        self.env_config = env_config
        self.git_service = git_service

    def init_on_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        theme = get_config_item_from_enum(ThemeEnum, self.env_config.theme)
        if theme is not None:
            self.theme_opt.setValue(theme.value)

        repo_type = get_config_item_from_enum(RepositoryTypeEnum, self.env_config.repository_type)
        if repo_type is not None:
            self.repository_type_opt.setValue(repo_type.value)

        git_method = get_config_item_from_enum(GitMethodEnum, self.env_config.git_method)
        if git_method is not None:
            self.git_method_opt.setValue(git_method.value)

        proxy_type = get_config_item_from_enum(ProxyTypeEnum, self.env_config.proxy_type)
        if proxy_type is not None:
            self.proxy_type_opt.setValue(proxy_type.value)

        self.personal_proxy_input.setValue(self.env_config.personal_proxy)

    def _on_theme_changed(self, index: int, value: str) -> None:
        """
        仓库类型改变
        :param index: 选项下标
        :param value: 值
        :return:
        """
        config_item = get_config_item_from_enum(ThemeEnum, value)
        self.env_config.theme = config_item.value
        setTheme(Theme[config_item.value.upper()])

    def _on_repo_type_changed(self, index: int, value: str) -> None:
        """
        仓库类型改变
        :param index: 选项下标
        :param value: 值
        :return:
        """
        config_item = get_config_item_from_enum(RepositoryTypeEnum, value)
        self.env_config.repository_type = config_item.value

    def _on_git_method_changed(self, index: int, value: str) -> None:
        """
        拉取方式改变
        :param index: 选项下标
        :param value: 值
        :return:
        """
        config_item = get_config_item_from_enum(GitMethodEnum, value)
        self.env_config.git_method = config_item.value

    def _on_proxy_type_changed(self, index: int, value: str) -> None:
        """
        拉取方式改变
        :param index: 选项下标
        :param value: 值
        :return:
        """
        config_item = get_config_item_from_enum(ProxyTypeEnum, value)
        self.env_config.proxy_type = config_item.value
        self._on_proxy_changed()

    def _on_personal_proxy_changed(self, value: str) -> None:
        """
        个人代理改变
        :param value: 值
        :return:
        """
        self.env_config.personal_proxy = value
        self._on_proxy_changed()

    def _on_proxy_changed(self) -> None:
        """
        代理发生改变
        :return:
        """
        self.git_service.is_proxy_set = False
