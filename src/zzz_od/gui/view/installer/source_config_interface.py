from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    FluentIcon, SettingCardGroup, StrongBodyLabel, BodyLabel, PrimaryPushButton,
    InfoBar, InfoBarPosition, PushButton, HyperlinkButton
)

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon.envs.env_config import ProxyTypeEnum, PipSourceEnum, CpythonSourceEnum, RepositoryTypeEnum, GitMethodEnum
from one_dragon_qt.widgets.base_interface import BaseInterface
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon_qt.widgets.setting_card.text_setting_card import TextSettingCard
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.utils.i18_utils import gt


class SourceConfigInterface(BaseInterface):
    """镜像源配置界面"""
    
    finished = Signal(bool)  # 完成信号
    
    def __init__(self, ctx: OneDragonEnvContext, parent=None):
        BaseInterface.__init__(
            self,
            object_name='source_config_interface',
            parent=parent,
            nav_text_cn='镜像源配置',
            nav_icon=FluentIcon.GLOBE
        )
        self.ctx = ctx
        
        self._init_ui()
        self._update_current_config()
    
    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # 标题
        title_label = StrongBodyLabel("配置镜像源")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 说明文本
        description = BodyLabel(
            "请根据您的网络环境，选择合适的代码仓库、网络代理和Python包源。\n"
            "正确的配置能够显著提升下载速度。"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(description)
        
        # 代码仓库设置
        self.git_group = SettingCardGroup("代码仓库设置")
        main_layout.addWidget(self.git_group)
        
        self.repository_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.CODE,
            title='代码仓库',
            content='选择代码源：GitHub（海外用户）或 Gitee（国内用户）',
            options_enum=RepositoryTypeEnum
        )
        self.repository_type_opt.value_changed.connect(self._on_repository_type_changed)
        self.git_group.addSettingCard(self.repository_type_opt)
        
        self.git_method_opt = ComboBoxSettingCard(
            icon=FluentIcon.LINK,
            title='克隆方式',
            content='HTTPS适合大多数用户，SSH需要配置密钥',
            options_enum=GitMethodEnum
        )
        self.git_method_opt.value_changed.connect(self._on_git_method_changed)
        self.git_group.addSettingCard(self.git_method_opt)
        
        # 网络代理设置
        self.proxy_group = SettingCardGroup("网络代理设置")
        main_layout.addWidget(self.proxy_group)
        
        self.proxy_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.GLOBE,
            title='代理类型',
            content='免费代理仅能加速工具和模型下载，无法加速代码同步',
            options_enum=ProxyTypeEnum
        )
        self.proxy_type_opt.value_changed.connect(self._on_proxy_type_changed)
        self.proxy_group.addSettingCard(self.proxy_type_opt)
        
        self.personal_proxy_input = TextSettingCard(
            icon=FluentIcon.WIFI,
            title='个人代理地址',
            input_placeholder='http://127.0.0.1:8080'
        )
        self.personal_proxy_input.value_changed.connect(self._on_personal_proxy_changed)
        self.proxy_group.addSettingCard(self.personal_proxy_input)
        
        self.gh_proxy_url_opt = TextSettingCard(
            icon=FluentIcon.GLOBE,
            title='免费代理地址'
        )
        self.gh_proxy_url_opt.value_changed.connect(self._on_gh_proxy_url_changed)
        self.proxy_group.addSettingCard(self.gh_proxy_url_opt)
        
        self.auto_fetch_gh_proxy_url_opt = SwitchSettingCard(
            icon=FluentIcon.SYNC,
            title='自动获取免费代理地址',
            content='获取失败时可前往 https://ghproxy.link/ 查看自行更新'
        )
        self.auto_fetch_gh_proxy_url_opt.value_changed.connect(self._on_auto_fetch_gh_proxy_url_changed)
        
        # 添加获取按钮和链接
        self.fetch_gh_proxy_url_btn = PushButton('获取', self)
        self.fetch_gh_proxy_url_btn.clicked.connect(self._on_fetch_gh_proxy_url_clicked)
        self.auto_fetch_gh_proxy_url_opt.hBoxLayout.addWidget(self.fetch_gh_proxy_url_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.auto_fetch_gh_proxy_url_opt.hBoxLayout.addSpacing(16)
        
        self.goto_gh_proxy_link_btn = HyperlinkButton('https://ghproxy.link', '前往', self)
        self.auto_fetch_gh_proxy_url_opt.hBoxLayout.addWidget(self.goto_gh_proxy_link_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.auto_fetch_gh_proxy_url_opt.hBoxLayout.addSpacing(16)
        
        self.proxy_group.addSettingCard(self.auto_fetch_gh_proxy_url_opt)
        
        # Python包源设置
        self.python_group = SettingCardGroup("Python包源设置")
        main_layout.addWidget(self.python_group)
        
        self.pip_source_opt = ComboBoxSettingCard(
            icon=FluentIcon.APPLICATION,
            title='Pip源',
            content='官方源（海外用户）或国内镜像源（国内用户）',
            options_enum=PipSourceEnum
        )
        self.pip_source_opt.value_changed.connect(self._on_pip_source_changed)
        self.python_group.addSettingCard(self.pip_source_opt)
        
        self.cpython_source_opt = ComboBoxSettingCard(
            icon=FluentIcon.DOWNLOAD,
            title='Python下载源',
            content='Python安装包下载源',
            options_enum=CpythonSourceEnum
        )
        self.cpython_source_opt.value_changed.connect(self._on_cpython_source_changed)
        self.python_group.addSettingCard(self.cpython_source_opt)
        
        # 确认按钮
        confirm_layout = QHBoxLayout()
        confirm_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confirm_layout.setSpacing(16)
        
        self.confirm_btn = PrimaryPushButton("确认配置")
        self.confirm_btn.setFixedSize(120, 40)
        self.confirm_btn.clicked.connect(self._confirm_config)
        confirm_layout.addWidget(self.confirm_btn)
        
        main_layout.addLayout(confirm_layout)
        main_layout.addStretch()
    
    def _update_current_config(self):
        """更新当前配置显示"""
        # 更新仓库类型
        repo_type = get_config_item_from_enum(RepositoryTypeEnum, self.ctx.env_config.repository_type)
        if repo_type is not None:
            self.repository_type_opt.setValue(repo_type.value)
        
        # 更新Git方法
        git_method = get_config_item_from_enum(GitMethodEnum, self.ctx.env_config.git_method)
        if git_method is not None:
            self.git_method_opt.setValue(git_method.value)
        
        # 更新代理类型
        proxy_type = get_config_item_from_enum(ProxyTypeEnum, self.ctx.env_config.proxy_type)
        if proxy_type is not None:
            self.proxy_type_opt.setValue(proxy_type.value)
        
        # 更新个人代理地址
        self.personal_proxy_input.setValue(self.ctx.env_config.personal_proxy)
        
        # 更新免费代理相关配置
        self.gh_proxy_url_opt.init_with_adapter(self.ctx.env_config.get_prop_adapter('gh_proxy_url'))
        self.auto_fetch_gh_proxy_url_opt.init_with_adapter(self.ctx.env_config.get_prop_adapter('auto_fetch_gh_proxy_url'))
        
        # 更新pip源
        self.pip_source_opt.init_with_adapter(self.ctx.env_config.get_prop_adapter('pip_source'))
        
        # 更新Python下载源
        self.cpython_source_opt.init_with_adapter(self.ctx.env_config.get_prop_adapter('cpython_source'))
        
        # 根据代理类型显示/隐藏相关界面元素
        self._update_proxy_ui()
    
    def _update_proxy_ui(self):
        """更新代理界面显示"""
        current_proxy_type = self.ctx.env_config.proxy_type
        
        # 根据代理类型显示/隐藏相关组件
        show_personal = current_proxy_type == ProxyTypeEnum.PERSONAL.value.value
        show_gh_proxy = current_proxy_type == ProxyTypeEnum.GHPROXY.value.value
        
        self.personal_proxy_input.setVisible(show_personal)
        self.gh_proxy_url_opt.setVisible(show_gh_proxy)
        self.auto_fetch_gh_proxy_url_opt.setVisible(show_gh_proxy)
    
    def _on_repository_type_changed(self, index: int, value: str):
        """仓库类型改变回调"""
        config_item = get_config_item_from_enum(RepositoryTypeEnum, value)
        self.ctx.env_config.repository_type = config_item.value
        self.ctx.git_service.update_git_remote()
    
    def _on_git_method_changed(self, index: int, value: str):
        """Git方法改变回调"""
        config_item = get_config_item_from_enum(GitMethodEnum, value)
        self.ctx.env_config.git_method = config_item.value
        self.ctx.git_service.update_git_remote()
    
    def _on_proxy_type_changed(self, index: int, value: str):
        """代理类型改变回调"""
        config_item = get_config_item_from_enum(ProxyTypeEnum, value)
        self.ctx.env_config.proxy_type = config_item.value
        self._update_proxy_ui()
        self._on_proxy_changed()
    
    def _on_personal_proxy_changed(self, value: str):
        """个人代理改变回调"""
        self.ctx.env_config.personal_proxy = value
        self._on_proxy_changed()
    
    def _on_gh_proxy_url_changed(self, value: str):
        """免费代理地址改变回调"""
        self.ctx.env_config.gh_proxy_url = value
        self._on_proxy_changed()
    
    def _on_auto_fetch_gh_proxy_url_changed(self, value: bool):
        """自动获取免费代理地址开关改变回调"""
        self.ctx.env_config.auto_fetch_gh_proxy_url = value
    
    def _on_proxy_changed(self):
        """代理发生改变"""
        # 清除当前代理设置的状态
        self.ctx.git_service.is_proxy_set = False
        # 调用 init_git_proxy 同步更新 Git 的代理设置
        self.ctx.git_service.init_git_proxy()
    
    def _on_pip_source_changed(self, index: int, value: str):
        """pip源改变回调"""
        pip_source = get_config_item_from_enum(PipSourceEnum, value)
        if pip_source is not None:
            self.ctx.env_config.pip_source = pip_source.value
    
    def _on_cpython_source_changed(self, index: int, value: str):
        """Python下载源改变回调"""
        cpython_source = get_config_item_from_enum(CpythonSourceEnum, value)
        if cpython_source is not None:
            self.ctx.env_config.cpython_source = cpython_source.value
    
    def _on_fetch_gh_proxy_url_clicked(self):
        """获取免费代理地址"""
        try:
            self.ctx.gh_proxy_service.update_proxy_url()
            self.gh_proxy_url_opt.init_with_adapter(self.ctx.env_config.get_prop_adapter('gh_proxy_url'))
            self._show_info_bar("✅ 获取成功", f"已更新免费代理地址: {self.ctx.env_config.gh_proxy_url}")
        except Exception as e:
            self._show_info_bar("❌ 获取失败", "请手动访问 https://ghproxy.link/ 获取最新地址")
    
    def _confirm_config(self):
        """确认配置"""
        self.finished.emit(True)
    
    def _show_info_bar(self, title: str, content: str, duration: int = 3000):
        """显示信息提示"""
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self,
        )
    
    def on_interface_shown(self) -> None:
        """界面显示时的回调"""
        BaseInterface.on_interface_shown(self)
    
    def on_interface_hidden(self) -> None:
        """界面隐藏时的回调"""
        BaseInterface.on_interface_hidden(self) 