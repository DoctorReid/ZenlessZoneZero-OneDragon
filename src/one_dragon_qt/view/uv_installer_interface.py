import os

from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from qfluentwidgets import ProgressRing, PrimaryPushButton, FluentIcon, SettingCardGroup, PushButton
from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon_qt.widgets.log_display_card import LogDisplayCard
from one_dragon_qt.widgets.install_card.all_install_card import AllInstallCard
from one_dragon_qt.widgets.install_card.code_install_card import CodeInstallCard
from one_dragon_qt.widgets.install_card.git_install_card import GitInstallCard
from one_dragon_qt.widgets.install_card.uv_install_card import UVInstallCard
from one_dragon_qt.widgets.install_card.uv_python_install_card import UVPythonInstallCard
from one_dragon_qt.widgets.install_card.uv_venv_install_card import UVVenvInstallCard
from one_dragon.utils.log_utils import log

class UVInstallerInterface(VerticalScrollInterface):
    def __init__(self, ctx: OneDragonEnvContext, parent=None):
        super().__init__(object_name='uv_install_interface',
                         parent=parent, content_widget=None,
                         nav_text_cn='一键安装', nav_icon=FluentIcon.DOWNLOAD)
        self.ctx: OneDragonEnvContext = ctx
        self._progress_value = 0
        self._progress_message = ''
        self._installing = False

    def get_content_widget(self) -> QWidget:
        content_widget = QWidget()
        main_vlayout = QVBoxLayout(content_widget)
        main_vlayout.setContentsMargins(0, 0, 0, 0)
        main_vlayout.setSpacing(0)

        center_hlayout = QHBoxLayout()
        center_hlayout.setContentsMargins(0, 0, 0, 0)
        center_hlayout.setSpacing(0)

        # 左logo区
        logo_widget = QWidget()
        logo_vlayout = QVBoxLayout(logo_widget)
        logo_vlayout.setContentsMargins(0, 0, 0, 0)
        logo_vlayout.setSpacing(0)
        logo_vlayout.addStretch(1)
        self.card_logo_label = QLabel()
        # WARNING! logo路径是以当前脚本运行路径定位的
        logo_path = os.path.abspath('../assets/ui/installer_logo.ico')
        log.info(f'绝对路径: {logo_path}, 存在: {os.path.exists(logo_path)}')
        log.info(f'logo绝对路径: {logo_path}, 存在: {os.path.exists(logo_path)}')
        card_logo_pixmap = QPixmap(logo_path)
        if card_logo_pixmap.isNull():
            log.error(f'Logo图片加载失败: {logo_path}')
        else:
            log.info(f'Logo图片加载成功: {logo_path}, size={card_logo_pixmap.size()}')
        self.card_logo_label.setPixmap(card_logo_pixmap.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.card_logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo_vlayout.addWidget(self.card_logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        logo_vlayout.addStretch(1)
        center_hlayout.addWidget(logo_widget, stretch=1)

        # 右按钮区
        button_widget = QWidget()
        button_vlayout = QVBoxLayout(button_widget)
        button_vlayout.setContentsMargins(0, 0, 0, 0)
        button_vlayout.setSpacing(24)
        button_vlayout.addStretch(1)
        self.install_btn = PrimaryPushButton('一键安装')
        self.install_btn.setFixedWidth(320)
        self.install_btn.setFixedHeight(60)
        font = self.install_btn.font()
        font.setPointSize(18)
        self.install_btn.setFont(font)
        button_vlayout.addWidget(self.install_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.progress_ring = ProgressRing()
        self.progress_ring.setFixedSize(64, 64)
        self.progress_ring.setVisible(False)
        button_vlayout.addWidget(self.progress_ring, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.progress_label = QLabel('')
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.progress_label.setVisible(False)
        button_vlayout.addWidget(self.progress_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        button_vlayout.addStretch(1)
        center_hlayout.addWidget(button_widget, stretch=2)

        main_vlayout.addStretch(1)
        main_vlayout.addLayout(center_hlayout)
        main_vlayout.addStretch(1)
        main_vlayout.addSpacing(40)

        # 高级安装
        self.advanced_label = QLabel('<a href="#" style="color:#0078D4;text-decoration:none;">↓ 高级安装</a>')
        self.advanced_label.setOpenExternalLinks(False)
        self.advanced_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.advanced_label.setStyleSheet('font-size:14px; margin:8px;')
        self.advanced_label.linkActivated.connect(self.show_advanced)
        main_vlayout.addWidget(self.advanced_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        # 返回按钮（高级安装界面时显示）
        self.back_btn = PushButton('返回一键安装')
        self.back_btn.setFixedWidth(160)
        self.back_btn.setFixedHeight(32)
        self.back_btn.setVisible(False)
        self.back_btn.clicked.connect(self.show_quick)
        main_vlayout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        # 高级安装卡片组
        self.git_opt = GitInstallCard(self.ctx)
        # self.git_opt.progress_changed.connect(self.update_progress)

        self.code_opt = CodeInstallCard(self.ctx)
        # self.code_opt.progress_changed.connect(self.update_progress)
        # self.code_opt.finished.connect(self._on_code_updated)

        self.uv_opt = UVInstallCard(self.ctx)
        # self.uv_opt.progress_changed.connect(self.update_progress)

        self.python_opt = UVPythonInstallCard(self.ctx)
        # self.python_opt.progress_changed.connect(self.update_progress)

        self.venv_opt = UVVenvInstallCard(self.ctx)
        # self.venv_opt.progress_changed.connect(self.update_progress)

        self.all_opt = AllInstallCard(self.ctx, [self.git_opt, self.code_opt, self.uv_opt, self.python_opt, self.venv_opt])

        self.update_group = SettingCardGroup('')
        self.update_group.titleLabel.setVisible(False)
        self.update_group.addSettingCard(self.all_opt)
        self.update_group.addSettingCard(self.git_opt)
        self.update_group.addSettingCard(self.code_opt)
        self.update_group.addSettingCard(self.uv_opt)
        self.update_group.addSettingCard(self.python_opt)
        self.update_group.addSettingCard(self.venv_opt)

        # v_layout.addWidget(self.update_group)
        self.update_group.setVisible(False)
        main_vlayout.addWidget(self.update_group)

        # 日志卡片
        self.log_card = LogDisplayCard()
        # v_layout.addWidget(self.log_card, stretch=1)
        self.log_card.setVisible(False)
        main_vlayout.addWidget(self.log_card)

        # 事件绑定
        self.install_btn.clicked.connect(self.on_install_clicked)

        return content_widget

    def on_install_clicked(self):
        self._installing = True
        self.install_btn.setVisible(False)
        self.progress_ring.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_ring.setValue(self._progress_value)
        self.progress_label.setText('安装中')
        self.all_opt.install_all(self.update_progress_ring)

    def update_progress_ring(self, progress: float, message: str):
        self._progress_value = int(progress * 100)
        self._progress_message = message or f'安装进度：{self._progress_value}%'
        self.progress_ring.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_ring.setValue(self._progress_value)
        self.progress_label.setText(self._progress_message)
        if progress >= 1.0:
            self.progress_label.setText('安装完成！')
            self._installing = False

    def show_advanced(self):
        self.card_logo_label.setVisible(False)
        self.install_btn.setVisible(False)
        self.progress_ring.setVisible(False)
        self.progress_label.setVisible(False)
        self.update_group.setVisible(True)
        self.log_card.setVisible(True)
        self.back_btn.setVisible(True)
        self.advanced_label.setVisible(False)

    def show_quick(self):
        self.card_logo_label.setVisible(True)
        self.install_btn.setVisible(not self._installing)
        self.progress_ring.setVisible(self._installing)
        self.progress_label.setVisible(self._installing)
        self.update_group.setVisible(False)
        self.log_card.setVisible(False)
        self.back_btn.setVisible(False)
        self.advanced_label.setVisible(True)
        if self._installing:
            self.progress_ring.setValue(self._progress_value)
            self.progress_label.setText(self._progress_message)
        else:
            self.progress_ring.setValue(0)
            self.progress_label.setText('')
            self.install_btn.setEnabled(True)

    def on_interface_shown(self) -> None:
        super().on_interface_shown()
        self.git_opt.check_and_update_display()
        self.code_opt.check_and_update_display()
        self.uv_opt.check_and_update_display()
        self.python_opt.check_and_update_display()
        self.venv_opt.check_and_update_display()
        self.log_card.start()

    def on_interface_hidden(self) -> None:
        super().on_interface_hidden()
        self.log_card.stop()
        
    # deprecated
    
    # def update_progress(self, progress: float, message: str) -> None:
    #     """
    #     进度回调更新
    #     :param progress: 进度 0~1
    #     :param message: 当前信息
    #     :return:
    #     """
    #     if progress == -1:
    #         self.progress_bar.setVisible(False)
    #         self.progress_bar_2.setVisible(True)
    #         self.progress_bar_2.start()
    #     else:
    #         self.progress_bar.setVisible(True)
    #         self.progress_bar.setVal(progress)
    #         self.progress_bar_2.setVisible(False)
    #         self.progress_bar_2.stop()
    # 
    # def _on_code_updated(self, success: bool) -> None:
    #     """
    #     代码更新后
    #     :param success:
    #     :return:
    #     """
    #     if success:
    #         self.venv_opt.check_and_update_display()
