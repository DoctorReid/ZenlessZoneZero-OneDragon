import os

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget, QFrame
from qfluentwidgets import (ProgressRing, PrimaryPushButton, FluentIcon, SettingCardGroup, 
                            PushButton, HyperlinkButton, ProgressBar, IndeterminateProgressBar, 
                            StrongBodyLabel, BodyLabel)

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


class ClickableStepCircle(QLabel):
    """可点击的步骤圆圈"""
    clicked = Signal(int)
    
    def __init__(self, step_index: int, parent=None):
        super().__init__(parent)
        self.step_index = step_index
        self.setFixedSize(30, 30)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.step_index)
        super().mousePressEvent(event)


class StepIndicator(QWidget):
    """步骤指示器组件"""
    
    step_clicked = Signal(int)
    
    def __init__(self, steps: list, parent=None):
        super().__init__(parent)
        self.steps = steps
        self.current_step = 0
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.step_widgets = []
        
        for i, step_name in enumerate(self.steps):
            # 创建步骤容器
            step_container = QWidget()
            step_layout = QVBoxLayout(step_container)
            step_layout.setContentsMargins(0, 0, 0, 0)
            step_layout.setSpacing(5)
            step_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 步骤圆圈
            circle = ClickableStepCircle(i)
            circle.setStyleSheet("""
                QLabel {
                    border: 2px solid #d0d0d0;
                    border-radius: 15px;
                    background-color: #f0f0f0;
                    color: #666;
                    font-weight: bold;
                }
            """)
            circle.setText(str(i + 1))
            circle.clicked.connect(self.on_step_clicked)
            
            # 步骤名称
            name_label = BodyLabel(step_name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("color: #666;")
            
            step_layout.addWidget(circle, alignment=Qt.AlignmentFlag.AlignCenter)
            step_layout.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
            self.step_widgets.append((circle, name_label))
            layout.addWidget(step_container)
            
            # 添加连接线
            if i < len(self.steps) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFixedHeight(2)
                line.setFixedWidth(50)
                line.setStyleSheet("background-color: #d0d0d0;")
                layout.addWidget(line)
    
    def on_step_clicked(self, step_index: int):
        self.step_clicked.emit(step_index)
    
    def set_current_step(self, step: int):
        self.current_step = step
        
        for i, (circle, name_label) in enumerate(self.step_widgets):
            if i < step:
                circle.setStyleSheet("""
                    QLabel {
                        border: 2px solid #00a86b;
                        border-radius: 15px;
                        background-color: #00a86b;
                        color: white;
                        font-weight: bold;
                        font-size: 16px;
                    }
                """)
                circle.setText("✓")
                name_label.setStyleSheet("color: #00a86b; font-weight: bold;")
            elif i == step:
                circle.setStyleSheet("""
                    QLabel {
                        border: 2px solid #0078d4;
                        border-radius: 15px;
                        background-color: #0078d4;
                        color: white;
                        font-weight: bold;
                        font-size: 14px;
                    }
                """)
                circle.setText(str(i + 1))
                name_label.setStyleSheet("color: #0078d4; font-weight: bold;")
            else:
                circle.setStyleSheet("""
                    QLabel {
                        border: 2px solid #d0d0d0;
                        border-radius: 15px;
                        background-color: #f0f0f0;
                        color: #666;
                        font-weight: bold;
                        font-size: 14px;
                    }
                """)
                circle.setText(str(i + 1))
                name_label.setStyleSheet("color: #666;")
    
    def set_step_skipped(self, step: int):
        if step < len(self.step_widgets):
            circle, name_label = self.step_widgets[step]
            circle.setStyleSheet("""
                QLabel {
                    border: 2px solid #ff8c00;
                    border-radius: 15px;
                    background-color: #ff8c00;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                }
            """)
            circle.setText("!")
            name_label.setStyleSheet("color: #ff8c00; font-weight: bold;")


class InstallStepWidget(QWidget):
    """单个安装步骤的界面"""
    
    step_completed = Signal(bool)
    step_skipped = Signal()
    
    def __init__(self, title: str, description: str, install_card, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.install_card = install_card
        self.is_completed = False
        self.is_skipped = False
        self.setup_ui()
        
        if self.install_card:
            self.install_card.finished.connect(self.on_install_finished)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title_label = StrongBodyLabel(self.title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(18)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # 描述
        desc_label = BodyLabel(self.description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 安装卡片
        if self.install_card:
            layout.addWidget(self.install_card)
        
        # 状态标签
        self.status_label = BodyLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
    
    def check_status(self):
        if self.install_card:
            self.install_card.check_and_update_display()
            self.update_status_from_card()
    
    def update_status_from_card(self):
        if not self.install_card:
            return
            
        try:
            icon, message = self.install_card.get_display_content()
            if any(keyword in message for keyword in ["已安装", "已同步", "已配置"]):
                self.is_completed = True
                self.status_label.setText("✓ 已满足条件")
                self.status_label.setStyleSheet("color: #00a86b; font-weight: bold;")
            elif any(keyword in message for keyword in ["未安装", "未同步", "未配置", "需更新"]):
                self.is_completed = False
                self.status_label.setText("需要安装或配置")
                self.status_label.setStyleSheet("color: #666;")
        except:
            pass
    
    def start_install(self):
        if self.install_card and not self.is_completed and not self.is_skipped:
            self.status_label.setText("正在安装...")
            self.status_label.setStyleSheet("color: #0078d4;")
            self.install_card.start_progress()
    
    def skip_step(self):
        self.is_skipped = True
        self.status_label.setText("⚠ 已跳过此步骤")
        self.status_label.setStyleSheet("color: #ff8c00; font-weight: bold;")
        self.step_skipped.emit()
    
    def on_install_finished(self, success: bool):
        self.is_completed = success
        
        if success:
            self.status_label.setText("✓ 安装完成")
            self.status_label.setStyleSheet("color: #00a86b; font-weight: bold;")
        else:
            self.status_label.setText("✗ 安装失败")
            self.status_label.setStyleSheet("color: #d13438; font-weight: bold;")
        
        self.step_completed.emit(success)


class UVInstallerInterface(VerticalScrollInterface):
    def __init__(self, ctx: OneDragonEnvContext, parent=None):
        VerticalScrollInterface.__init__(self, object_name='uv_install_interface',
                                         parent=parent, content_widget=None,
                                         nav_text_cn='一键安装', nav_icon=FluentIcon.DOWNLOAD)
        self.ctx: OneDragonEnvContext = ctx
        self._progress_value = 0
        self._progress_message = ''
        self._installing = False
        
        # 高级安装模式相关属性
        self.current_step = 0
        self.install_steps = []
        self.is_all_completed = False
        self.is_advanced_mode = False

    def get_content_widget(self) -> QWidget:
        content_widget = QWidget()
        
        # 使用QStackedWidget来切换两种布局
        self.main_stack = QStackedWidget(content_widget)
        
        # 创建基础界面
        self.basic_widget = self.create_basic_widget()
        self.main_stack.addWidget(self.basic_widget)
        
        # 创建高级界面
        self.advanced_widget = self.create_advanced_widget()
        self.main_stack.addWidget(self.advanced_widget)
        
        # 设置布局
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_stack)
        
        return content_widget

    def create_basic_widget(self) -> QWidget:
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
        logo_path = os.path.abspath('assets/ui/installer_logo.ico')
        log.info(f'绝对路径: {logo_path}, 存在: {os.path.exists(logo_path)}')
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
        self.advanced_btn = HyperlinkButton('', '自定义安装')
        self.advanced_btn.clicked.connect(self.show_advanced)
        main_vlayout.addWidget(self.advanced_btn, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        # 高级安装卡片组
        self.git_opt = GitInstallCard(self.ctx)
        self.code_opt = CodeInstallCard(self.ctx)
        self.uv_opt = UVInstallCard(self.ctx)
        self.python_opt = UVPythonInstallCard(self.ctx)
        self.venv_opt = UVVenvInstallCard(self.ctx)

        self.all_opt = AllInstallCard(self.ctx, [self.git_opt, self.code_opt, self.uv_opt, self.python_opt, self.venv_opt])

        # 事件绑定
        self.install_btn.clicked.connect(self.on_install_clicked)

        return content_widget

    def create_advanced_widget(self) -> QWidget:
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # 顶部标题
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        header_layout.setSpacing(10)
        
        # 主标题
        title_label = StrongBodyLabel("一条龙安装向导")
        title_font = title_label.font()
        title_font.setPointSize(24)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        main_layout.addWidget(header_widget)

        # 返回按钮
        self.back_btn = HyperlinkButton('', '返回')
        self.back_btn.clicked.connect(self.show_quick)
        main_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # 步骤指示器
        step_names = ["Git环境", "代码同步", "UV工具", "Python环境", "依赖安装"]
        self.step_indicator = StepIndicator(step_names)
        self.step_indicator.step_clicked.connect(self.on_step_indicator_clicked)
        main_layout.addWidget(self.step_indicator)

        # 创建安装步骤
        self.install_steps = [
            InstallStepWidget(
                "Git环境配置",
                "Git是代码版本管理工具，用于下载和更新项目代码。\n如果您已安装Git，系统会自动检测；否则将为您安装。",
                self.git_opt
            ),
            InstallStepWidget(
                "代码同步",
                "从远程仓库同步最新的项目代码。\n确保您使用的是最新版本的功能和修复。",
                self.code_opt
            ),
            InstallStepWidget(
                "UV工具安装",
                "UV是现代化的Python包管理工具，比pip更快更可靠。\n用于管理Python环境和依赖包。",
                self.uv_opt
            ),
            InstallStepWidget(
                "Python环境配置",
                "配置Python虚拟环境，确保项目运行在独立的环境中。\n避免与系统Python环境冲突。",
                self.python_opt
            ),
            InstallStepWidget(
                "依赖安装",
                "安装项目运行所需的所有Python依赖包。\n这可能需要几分钟时间，请耐心等待。",
                self.venv_opt
            )
        ]

        # 连接步骤完成信号
        for step in self.install_steps:
            step.step_completed.connect(self.on_step_completed)
            step.step_skipped.connect(self.on_step_skipped)

        # 步骤内容区域
        self.step_stack = QStackedWidget()
        for step in self.install_steps:
            self.step_stack.addWidget(step)
        main_layout.addWidget(self.step_stack, stretch=1)

        # 底部按钮区域
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 上一步按钮
        self.prev_btn = PushButton("上一步")
        self.prev_btn.setFixedSize(120, 40)
        self.prev_btn.clicked.connect(self.go_previous_step)
        self.prev_btn.setEnabled(False)
        
        button_layout.addStretch()
        button_layout.addWidget(self.prev_btn)
        
        # 开始安装按钮
        self.install_step_btn = PrimaryPushButton("开始安装")
        self.install_step_btn.setFixedSize(120, 40)
        self.install_step_btn.clicked.connect(self.start_current_install)
        button_layout.addWidget(self.install_step_btn)
        
        # 跳过当前步骤按钮
        self.skip_current_btn = PushButton("跳过此步骤")
        self.skip_current_btn.setFixedSize(120, 40)
        self.skip_current_btn.clicked.connect(self.skip_current_step)
        button_layout.addWidget(self.skip_current_btn)
        
        # 下一步按钮
        self.next_btn = PushButton("下一步")
        self.next_btn.setFixedSize(120, 40)
        self.next_btn.clicked.connect(self.go_next_step)
        button_layout.addWidget(self.next_btn)
        
        main_layout.addWidget(button_widget)

        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.progress_bar_2 = IndeterminateProgressBar()
        self.progress_bar_2.setVisible(False)
        main_layout.addWidget(self.progress_bar_2)

        # 连接进度信号
        for card in [self.git_opt, self.code_opt, self.uv_opt, self.python_opt, self.venv_opt]:
            card.progress_changed.connect(self.update_progress)

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
        """切换到高级安装界面"""
        self.is_advanced_mode = True
        self.main_stack.setCurrentIndex(1)
        # 初始化高级界面显示
        self.update_step_display()

    def show_quick(self):
        """返回基础安装界面"""
        self.is_advanced_mode = False
        self.main_stack.setCurrentIndex(0)

    def update_step_display(self):
        """更新步骤显示"""
        if not self.is_advanced_mode:
            return
            
        self.update_step_indicator()
        self.step_stack.setCurrentIndex(self.current_step)
        
        # 更新按钮状态
        self.prev_btn.setEnabled(self.current_step > 0)
        
        # 获取当前步骤
        current_step_widget = self.install_steps[self.current_step]
        
        if not current_step_widget.is_completed and not current_step_widget.is_skipped:
            current_step_widget.check_status()
        
        if self.is_all_completed:
            self.next_btn.clicked.disconnect()
            self.next_btn.clicked.connect(self.go_next_step)
            self.is_all_completed = False
        
        # 根据当前步骤状态更新按钮
        if current_step_widget.is_completed:
            self.install_step_btn.setVisible(False)
            self.skip_current_btn.setVisible(False)
            self.next_btn.setVisible(True)
            self.next_btn.setEnabled(True)
            if self.current_step == len(self.install_steps) - 1:
                self.next_btn.setText("完成")
            else:
                self.next_btn.setText("下一步")
        elif current_step_widget.is_skipped:
            self.install_step_btn.setVisible(False)
            self.skip_current_btn.setVisible(False)
            self.next_btn.setVisible(True)
            self.next_btn.setEnabled(True)
            if self.current_step == len(self.install_steps) - 1:
                self.next_btn.setText("完成")
            else:
                self.next_btn.setText("下一步")
        else:
            self.install_step_btn.setVisible(True)
            self.skip_current_btn.setVisible(True)
            self.next_btn.setVisible(False)

    def update_step_indicator(self):
        """更新步骤指示器"""
        self.step_indicator.set_current_step(self.current_step)
        
        for i, step in enumerate(self.install_steps):
            if step.is_skipped:
                self.step_indicator.set_step_skipped(i)

    def start_current_install(self):
        """开始当前步骤的安装"""
        current_step_widget = self.install_steps[self.current_step]
        current_step_widget.start_install()

    def go_previous_step(self):
        """上一步"""
        if self.current_step > 0:
            if self.is_all_completed:
                self.is_all_completed = False
                self.next_btn.clicked.disconnect()
                self.next_btn.clicked.connect(self.go_next_step)
            
            self.current_step -= 1
            self.update_step_display()

    def go_next_step(self):
        """下一步"""
        current_step_widget = self.install_steps[self.current_step]
        
        if current_step_widget.is_completed or current_step_widget.is_skipped:
            if self.current_step < len(self.install_steps) - 1:
                self.current_step += 1
                self.update_step_display()
            else:
                self.show_completion_message()

    def skip_current_step(self):
        """跳过当前步骤"""
        current_step_widget = self.install_steps[self.current_step]
        if not current_step_widget.is_completed and not current_step_widget.is_skipped:
            current_step_widget.skip_step()

    def on_step_completed(self, success: bool):
        """步骤完成回调"""
        self.update_step_display()
        if success and self.current_step < len(self.install_steps) - 1:
            QTimer.singleShot(1000, self.auto_next_step)

    def auto_next_step(self):
        """自动进入下一步"""
        if self.current_step < len(self.install_steps) - 1:
            self.current_step += 1
            self.update_step_display()

    def on_step_skipped(self):
        """步骤跳过回调"""
        self.step_indicator.set_step_skipped(self.current_step)
        self.update_step_display()
        if self.current_step < len(self.install_steps) - 1:
            QTimer.singleShot(500, self.auto_next_step)

    def show_completion_message(self):
        """显示完成消息"""
        self.is_all_completed = True
        self.next_btn.setText("启动程序")
        self.next_btn.clicked.disconnect()
        self.next_btn.clicked.connect(self.launch_application)

    def launch_application(self):
        """启动应用程序"""
        pass

    def on_step_indicator_clicked(self, step_index: int):
        """处理步骤指示器点击事件"""
        can_jump = False
        
        if step_index <= self.current_step:
            can_jump = True
        elif step_index < len(self.install_steps):
            can_jump = True
            for i in range(self.current_step + 1, step_index + 1):
                step_widget = self.install_steps[i]
                if not (step_widget.is_completed or step_widget.is_skipped):
                    can_jump = False
                    break
        
        if can_jump:
            if self.is_all_completed:
                self.is_all_completed = False
                self.next_btn.clicked.disconnect()
                self.next_btn.clicked.connect(self.go_next_step)
            
            self.current_step = step_index
            self.update_step_display()

    def update_progress(self, progress: float, message: str) -> None:
        """进度回调更新"""
        if not self.is_advanced_mode:
            return
            
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
        """代码更新后"""
        if success:
            self.venv_opt.check_and_update_display()

    def on_interface_shown(self) -> None:
        super().on_interface_shown()
        self.git_opt.check_and_update_display()
        self.code_opt.check_and_update_display()
        self.uv_opt.check_and_update_display()
        self.python_opt.check_and_update_display()
        self.venv_opt.check_and_update_display()
        
        # 如果是高级模式，检查所有步骤的状态
        if self.is_advanced_mode:
            for step in self.install_steps:
                step.check_status()

    def on_interface_hidden(self) -> None:
        super().on_interface_hidden()
