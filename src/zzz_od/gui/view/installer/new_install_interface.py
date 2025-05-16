from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import ProgressBar, IndeterminateProgressBar, SettingCardGroup, FluentIcon, PushButton

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon_qt.widgets.log_display_card import LogDisplayCard
from one_dragon_qt.widgets.install_card.all_install_card import AllInstallCard
from one_dragon_qt.widgets.install_card.code_install_card import CodeInstallCard
from one_dragon_qt.widgets.install_card.git_install_card import GitInstallCard
from one_dragon_qt.widgets.install_card.python_install_card import PythonInstallCard
from one_dragon_qt.widgets.install_card.venv_install_card import VenvInstallCard
from one_dragon.utils.i18_utils import gt
from zzz_od.gui.view.installer.uv_uv_install_card import UvUvInstallCard

class NewInstallInterface(VerticalScrollInterface):
    def __init__(self, ctx: OneDragonEnvContext, parent=None):
        VerticalScrollInterface.__init__(self, object_name='new_install_interface',
                                         parent=parent, content_widget=None,
                                         nav_text_cn='一键安装(uv)', nav_icon=FluentIcon.CLOUD_DOWNLOAD)
        self.ctx: OneDragonEnvContext = ctx

    def get_content_widget(self) -> QWidget:
        content_widget = QWidget()
        v_layout = QVBoxLayout(content_widget)

        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setVisible(False)
        v_layout.addWidget(self.progress_bar)

        self.progress_bar_2 = IndeterminateProgressBar()
        self.progress_bar_2.setVisible(False)
        v_layout.addWidget(self.progress_bar_2)

        self.git_opt = GitInstallCard(self.ctx)
        self.git_opt.progress_changed.connect(self.update_progress)

        self.code_opt = CodeInstallCard(self.ctx)
        self.code_opt.progress_changed.connect(self.update_progress)
        self.code_opt.finished.connect(self._on_code_updated)

        self.python_opt = PythonInstallCard(self.ctx)
        self.python_opt.progress_changed.connect(self.update_progress)

        self.venv_opt = VenvInstallCard(self.ctx)
        self.venv_opt.progress_changed.connect(self.update_progress)

        self.uv_opt = UvUvInstallCard(self.ctx)
        self.uv_opt.progress_changed.connect(self.update_progress)

        self.all_opt = AllInstallCard(self.ctx, [self.git_opt, self.code_opt, self.python_opt, self.venv_opt])


        self.uv_all_btn = PushButton(text=gt('uv一键安装', 'ui'))
        self.uv_all_btn.clicked.connect(self.uv_all_install)

        # 新建水平布局，放两个按钮，并加到主布局顶部
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.all_opt.install_btn)
        btn_layout.addWidget(self.uv_all_btn)
        v_layout.addLayout(btn_layout)

        update_group = SettingCardGroup(gt('运行环境', 'ui'))
        update_group.addSettingCard(self.all_opt)
        update_group.addSettingCard(self.git_opt)
        update_group.addSettingCard(self.code_opt)
        update_group.addSettingCard(self.python_opt)
        update_group.addSettingCard(self.venv_opt)
        update_group.addSettingCard(self.uv_opt)

        v_layout.addWidget(update_group)
        log_group = SettingCardGroup(gt('安装日志', 'ui'))
        v_layout.addWidget(log_group)
        self.log_card = LogDisplayCard()
        v_layout.addWidget(self.log_card, stretch=1)

        return content_widget

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)
        self.git_opt.check_and_update_display()
        self.code_opt.check_and_update_display()
        self.python_opt.check_and_update_display()
        self.venv_opt.check_and_update_display()
        self.uv_opt.check_and_update_display()
        self.log_card.start()

    def on_interface_hidden(self) -> None:
        VerticalScrollInterface.on_interface_hidden(self)
        self.log_card.stop()

    def update_progress(self, progress: float, message: str) -> None:
        if progress == -1:
            self.progress_bar.setVisible(False)
            self.progress_bar_2.setVisible(True)
            self.progress_bar_2.start()
        else:
            self.progress_bar.setVisible(True)
            self.progress_bar.setVal(progress)
            self.progress_bar_2.setVisible(False)
            self.progress_bar_2.stop()

    def _on_code_updated(self, success: bool) -> None:
        if success:
            self.venv_opt.check_and_update_display()

    def uv_all_install(self):
        """
        依次用uv方式安装所有支持的卡片
        """
        install_methods = []
        for card in [self.git_opt, self.code_opt, self.python_opt, self.venv_opt, self.uv_opt]:
            if hasattr(card, 'uv_install_requirements'):
                install_methods.append(card.uv_install_requirements)
            elif hasattr(card, 'uv_install_python_venv'):
                install_methods.append(card.uv_install_python_venv)
            elif hasattr(card, 'uv_install_uv'):
                install_methods.append(card.uv_install_uv)
            elif hasattr(card, 'uv_install_git'):
                install_methods.append(card.uv_install_git)
        self._run_uv_install_methods(install_methods)

    def _run_uv_install_methods(self, methods):
        """
        顺序执行所有uv安装方法
        """
        if not methods:
            return
        def next_install(idx):
            if idx >= len(methods):
                self.progress_bar.setVisible(False)
                self.progress_bar_2.setVisible(False)
                return
            def progress_callback(progress, msg):
                self.update_progress(progress, msg)
            result = methods[idx](progress_callback)
            if isinstance(result, tuple) and result[0]:
                next_install(idx+1)
            else:
                self.progress_bar.setVisible(False)
                self.progress_bar_2.setVisible(False)
        next_install(0) 