from one_dragon.gui.component.interface.base_interface import BaseInterface
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface


class SettingOneDragonInterface(VerticalScrollInterface):

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