from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from qfluentwidgets import ProgressBar, IndeterminateProgressBar, SettingCardGroup, FluentIcon, PushButton, PrimaryPushButton

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon_qt.widgets.log_display_card import LogDisplayCard
from one_dragon_qt.widgets.install_card.all_install_card import AllInstallCard
from one_dragon_qt.widgets.install_card.code_install_card import CodeInstallCard
from one_dragon_qt.widgets.install_card.git_install_card import GitInstallCard
from one_dragon_qt.widgets.install_card.uv_install_card import UVInstallCard
from one_dragon_qt.widgets.install_card.uv_python_install_card import UVPythonInstallCard
from one_dragon_qt.widgets.install_card.uv_venv_install_card import UVVenvInstallCard

class UVInstallerInterface(VerticalScrollInterface):
    def __init__(self, ctx: OneDragonEnvContext, parent=None):
        VerticalScrollInterface.__init__(self, object_name='uv_install_interface',
                                         parent=parent, content_widget=None,
                                         nav_text_cn='一键安装', nav_icon=FluentIcon.DOWNLOAD)
        self.ctx: OneDragonEnvContext = ctx

    def get_content_widget(self) -> QWidget:
        content_widget = QWidget()
        v_layout = QVBoxLayout(content_widget)

        # 一键安装
        self.quick_group = QWidget()
        quick_layout = QVBoxLayout(self.quick_group)
        quick_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo_label = QLabel()
        logo_pixmap = QPixmap('assets/ui/installer_logo.ico')
        logo_label.setPixmap(logo_pixmap.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        quick_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.install_btn = PrimaryPushButton('一键安装')
        self.install_btn.setFixedWidth(360)
        self.install_btn.setFixedHeight(72)
        font = self.install_btn.font()
        font.setPointSize(20)
        self.install_btn.setFont(font)
        quick_layout.addWidget(self.install_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.advanced_btn = PushButton('高级安装')
        self.advanced_btn.setFixedWidth(200)
        self.advanced_btn.setFixedHeight(40)
        adv_font = self.advanced_btn.font()
        adv_font.setPointSize(10)
        self.advanced_btn.setFont(adv_font)
        quick_layout.addWidget(self.advanced_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        v_layout.addWidget(self.quick_group)
        self.quick_group.setVisible(True)

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

        self.uv_opt = UVInstallCard(self.ctx)
        self.uv_opt.progress_changed.connect(self.update_progress)

        self.python_opt = UVPythonInstallCard(self.ctx)
        self.python_opt.progress_changed.connect(self.update_progress)

        self.venv_opt = UVVenvInstallCard(self.ctx)
        self.venv_opt.progress_changed.connect(self.update_progress)

        self.all_opt = AllInstallCard(self.ctx, [self.git_opt, self.code_opt, self.uv_opt, self.python_opt, self.venv_opt])

        self.update_group = SettingCardGroup('')
        self.update_group.titleLabel.setVisible(False)
        self.update_group.addSettingCard(self.all_opt)
        self.update_group.addSettingCard(self.git_opt)
        self.update_group.addSettingCard(self.code_opt)
        self.update_group.addSettingCard(self.uv_opt)
        self.update_group.addSettingCard(self.python_opt)
        self.update_group.addSettingCard(self.venv_opt)

        v_layout.addWidget(self.update_group)
        self.update_group.setVisible(False)

        self.log_card = LogDisplayCard()
        v_layout.addWidget(self.log_card, stretch=1)
        self.log_card.setVisible(False)

        self.advanced_btn.clicked.connect(lambda: self.update_display(False))

        self.back_btn = PushButton('返回一键安装')
        self.back_btn.setFixedWidth(200)
        self.back_btn.setFixedHeight(32)
        v_layout.insertWidget(v_layout.indexOf(self.update_group), self.back_btn)
        self.back_btn.setVisible(False)
        self.back_btn.clicked.connect(lambda: self.update_display(True))

        self.install_btn.clicked.connect(lambda: self.all_opt.install_all(self.update_progress))

        return content_widget

    def update_display(self, value: bool) -> None:
        self.quick_group.setVisible(value)
        self.update_group.setVisible(not value)
        self.log_card.setVisible(not value)
        self.back_btn.setVisible(not value)

    def on_interface_shown(self) -> None:
        """
        页面加载完成后 检测各个组件状态并更新显示
        :return:
        """
        VerticalScrollInterface.on_interface_shown(self)
        self.git_opt.check_and_update_display()
        self.code_opt.check_and_update_display()
        self.uv_opt.check_and_update_display()
        self.python_opt.check_and_update_display()
        self.venv_opt.check_and_update_display()
        self.log_card.start()  # 开始日志更新

    def on_interface_hidden(self) -> None:
        """
        子界面隐藏时的回调
        :return:
        """
        VerticalScrollInterface.on_interface_hidden(self)
        self.log_card.stop()  # 开始日志更新

    def update_progress(self, progress: float, message: str) -> None:
        """
        进度回调更新
        :param progress: 进度 0~1
        :param message: 当前信息
        :return:
        """
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
        """
        代码更新后
        :param success:
        :return:
        """
        if success:
            self.venv_opt.check_and_update_display()
