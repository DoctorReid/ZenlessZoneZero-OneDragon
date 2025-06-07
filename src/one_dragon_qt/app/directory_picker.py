import os
from PySide6.QtCore import QSize, Qt, QEventLoop
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog, QApplication, QWidget
from PySide6.QtGui import QPixmap
from qfluentwidgets import (SplashScreen, FluentIcon, PrimaryPushButton, LineEdit,
                            SplitTitleBar, MessageBox, SubtitleLabel, PixmapLabel)
from one_dragon_qt.windows.window import PhosWindow
from one_dragon_qt.services.styles_manager import OdQtStyleSheet


class DirectoryPickerInterface(QWidget):
    """路径选择器界面"""

    def __init__(self, parent=None, icon_path=None):
        QWidget.__init__(self, parent=parent)
        self.setObjectName("directory_picker_interface")
        self.selected_path = ""
        self.icon_path = icon_path
        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 10, 40, 40)
        main_layout.setSpacing(20)

        # 图标区域
        if self.icon_path:
            icon_label = PixmapLabel()
            pixmap = QPixmap(self.icon_path)
            if not pixmap.isNull():
                pixel_ratio = self.devicePixelRatio()
                target_size = QSize(96, 96)
                scaled_pixmap = pixmap.scaled(
                    target_size * pixel_ratio,
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                scaled_pixmap.setDevicePixelRatio(pixel_ratio)
                icon_label.setPixmap(scaled_pixmap)
                icon_label.setFixedSize(target_size)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                main_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 标题
        title_label = SubtitleLabel("请选择安装路径")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 路径显示区域
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)

        self.path_input = LineEdit()
        self.path_input.setPlaceholderText("选择安装路径...")
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input)
        self.browse_btn = PrimaryPushButton("浏览")
        self.browse_btn.setIcon(FluentIcon.FOLDER_ADD)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        path_layout.addWidget(self.browse_btn)

        main_layout.addLayout(path_layout)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        self.confirm_btn = PrimaryPushButton("确认")
        self.confirm_btn.setIcon(FluentIcon.ACCEPT)
        self.confirm_btn.setMinimumSize(120, 36)  # 设置最小尺寸使按钮变大
        self.confirm_btn.clicked.connect(self._on_confirm_clicked)
        self.confirm_btn.setEnabled(False)
        button_layout.addWidget(self.confirm_btn)
        button_layout.addStretch(1)

        main_layout.addLayout(button_layout)

        # 添加弹性空间
        main_layout.addStretch(1)

    def _on_browse_clicked(self):
        """浏览按钮点击事件"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择目录",
            "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )

        if directory:
            # 检查路径是否为全英文或者包含空格
            if not all(c.isascii() for c in directory) or ' ' in directory:
                # 显示警告对话框
                w = MessageBox(
                    "警告",
                    "所选目录包含非英文字符或空格，请确保路径全为英文且不包含空格。",
                    parent=self.window(),
                )
                w.yesButton.setText("我知道了")
                w.cancelButton.setVisible(False)
                w.exec()
                self.selected_path = ""
                self.path_input.clear()
                self.confirm_btn.setEnabled(False)
                return

            # 检查目录是否为空
            if os.listdir(directory):
                # 目录不为空，显示警告对话框
                w = MessageBox(
                    title="警告",
                    content=f"所选目录不为空：\n{directory}\n\n是否继续使用此目录？",
                    parent=self.window(),
                )
                w.yesButton.setText("继续使用")
                w.cancelButton.setText("选择其他目录")
                if w.exec():
                    self.selected_path = directory
                    self.path_input.setText(directory)
                    self.confirm_btn.setEnabled(True)
            else:
                # 目录为空，直接使用
                self.selected_path = directory
                self.path_input.setText(directory)
                self.confirm_btn.setEnabled(True)

    def _on_confirm_clicked(self):
        """确认按钮点击事件"""
        if self.selected_path:
            # 获取顶层窗口
            window = self.window()
            if isinstance(window, DirectoryPickerWindow):
                window.selected_directory = self.selected_path
                window.close()


class DirectoryPickerWindow(PhosWindow):

    def __init__(self,
                 win_title: str,
                 parent=None,
                 icon_path=None):
        PhosWindow.__init__(self, parent=parent)
        self.setTitleBar(SplitTitleBar(self))
        self._last_stack_idx: int = 0
        self.selected_directory: str = ""
        self.icon_path = icon_path

        # 设置窗口标题
        self.setWindowTitle(win_title)

        # 设置为模态窗口
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # 初始化窗口
        self.init_window()

        # 创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(144, 144))

        # 在创建其他子页面前先显示主界面
        self.show()

        self.create_sub_interface()

        # 隐藏启动页面
        self.splashScreen.finish()

    def exec(self):
        """模态执行窗口，等待窗口关闭"""
        self._event_loop = QEventLoop()
        self._event_loop.exec()
        return True if self.selected_directory else False

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 如果没有选择目录，退出程序
        if not self.selected_directory:
            QApplication.quit()

        # 退出事件循环
        if hasattr(self, '_event_loop') and self._event_loop.isRunning():
            self._event_loop.quit()

        event.accept()

    def create_sub_interface(self) -> None:
        """
        创建子页面
        :return:
        """
        # 创建路径选择器界面，传入图标路径
        self.picker_interface = DirectoryPickerInterface(self, self.icon_path)
        self.addSubInterface(self.picker_interface, FluentIcon.FOLDER_ADD, "")

    def init_window(self):
        self.resize(600, 240)
        self.move(100, 100)

        # 布局样式调整
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.stackedWidget.setContentsMargins(0, 28, 0, 0)
        self.navigationInterface.setContentsMargins(0, 28, 0, 0)

        # 配置样式
        OdQtStyleSheet.APP_WINDOW.apply(self)
        OdQtStyleSheet.NAVIGATION_INTERFACE.apply(self.navigationInterface)
        OdQtStyleSheet.STACKED_WIDGET.apply(self.stackedWidget)
        OdQtStyleSheet.TITLE_BAR.apply(self.titleBar)

        self.navigationInterface.setVisible(False)
