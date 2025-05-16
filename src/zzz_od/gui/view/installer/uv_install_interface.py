from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ProgressBar, IndeterminateProgressBar, SettingCardGroup, FluentIcon

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from zzz_od.gui.view.installer.uv_log_display_card import UvLogDisplayCard
from zzz_od.gui.view.installer.uv_all_install_card import UvAllInstallCard
from zzz_od.gui.view.installer.uv_code_install_card import UvCodeInstallCard
from zzz_od.gui.view.installer.uv_git_install_card import UvGitInstallCard
from zzz_od.gui.view.installer.uv_python_install_card import UvPythonInstallCard
from zzz_od.gui.view.installer.uv_venv_install_card import UvVenvInstallCard
from one_dragon.utils.i18_utils import gt

class UvInstallInterface(VerticalScrollInterface):
    def __init__(self, ctx: OneDragonEnvContext, parent=None):
        VerticalScrollInterface.__init__(self, object_name='uv_install_interface',
                                         parent=parent, content_widget=None,
                                         nav_text_cn='安装(Beta)', nav_icon=FluentIcon.DOWNLOAD)
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

        self.git_opt = UvGitInstallCard(self.ctx)
        self.git_opt.progress_changed.connect(self.update_progress)

        self.code_opt = UvCodeInstallCard(self.ctx)
        self.code_opt.progress_changed.connect(self.update_progress)
        self.code_opt.finished.connect(self._on_code_updated)

        self.python_opt = UvPythonInstallCard(self.ctx)
        self.python_opt.progress_changed.connect(self.update_progress)

        self.venv_opt = UvVenvInstallCard(self.ctx)
        self.venv_opt.progress_changed.connect(self.update_progress)

        self.all_opt = UvAllInstallCard(self.ctx, [self.git_opt, self.code_opt, self.python_opt, self.venv_opt])

        update_group = SettingCardGroup(gt('运行环境', 'ui'))
        update_group.addSettingCard(self.all_opt)
        update_group.addSettingCard(self.git_opt)
        update_group.addSettingCard(self.code_opt)
        update_group.addSettingCard(self.python_opt)
        update_group.addSettingCard(self.venv_opt)

        v_layout.addWidget(update_group)
        log_group = SettingCardGroup(gt('安装日志', 'ui'))
        v_layout.addWidget(log_group)
        self.log_card = UvLogDisplayCard()
        v_layout.addWidget(self.log_card, stretch=1)

        return content_widget

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)
        self.git_opt.check_and_update_display()
        self.code_opt.check_and_update_display()
        self.python_opt.check_and_update_display()
        self.venv_opt.check_and_update_display()
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