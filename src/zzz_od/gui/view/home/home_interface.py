import os
from PySide6.QtCore import Qt, QThread, Signal, QSize, QUrl
from PySide6.QtGui import (
    QFont,
    QDesktopServices, QColor
)
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
)
from qfluentwidgets import (
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    Dialog,
    SimpleCardWidget,
    PrimaryPushButton,
)
from typing import Callable, Optional

from one_dragon.base.operation.operation import Operation
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.gui.widgets.vertical_scroll_interface import (
    VerticalScrollInterface,
)
from one_dragon.gui.windows.app_window_base import AppWindowBase
from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from phosdeiz.gui.services import PhosStyleSheet
from phosdeiz.gui.widgets import IconButton, NoticeCard, GameDialog, Banner
from phosdeiz.gui.windows.window import PhosTitleBar
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.enter_game.open_game import OpenGame


class ButtonGroup(SimpleCardWidget):
    """显示主页和 GitHub 按钮的竖直按钮组"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setFixedSize(56, 320)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # 创建主页按钮
        home_button = IconButton(
            FluentIcon.HOME.icon(color=QColor("#fff")),
            tip_title="一条龙官网",
            tip_content="使用说明都能在这找到",
            isTooltip=True,
        )
        home_button.setIconSize(QSize(32, 32))
        home_button.clicked.connect(self.open_home)
        layout.addWidget(home_button)

        # 创建 GitHub 按钮
        github_button = IconButton(
            FluentIcon.GITHUB.icon(color=QColor("#fff")),
            tip_title="Github仓库",
            tip_content="如果本项目有帮助到您~\n不妨给项目点一个Star⭐",
            isTooltip=True,
        )
        github_button.setIconSize(QSize(32, 32))
        github_button.clicked.connect(self.open_github)
        layout.addWidget(github_button)

        # 添加一个可伸缩的空白区域
        layout.addStretch()

        # 创建 同步 按钮
        sync_button = IconButton(
            FluentIcon.SYNC.icon(color=QColor("#fff")), tip_title="未完工", tip_content="开发中", isTooltip=True
        )
        sync_button.setIconSize(QSize(32, 32))
        layout.addWidget(sync_button)
        
    def _normalBackgroundColor(self):
        return QColor(0, 0, 0, 33)

    def open_home(self):
        """打开主页链接"""
        QDesktopServices.openUrl(QUrl("https://one-dragon.org/zzz/zh/home.html"))

    def open_github(self):
        """打开 GitHub 链接"""
        QDesktopServices.openUrl(
            QUrl("https://github.com/DoctorReid/ZenlessZoneZero-OneDragon")
        )


class CheckRunnerBase(QThread):
    """检查更新的基础线程类"""

    need_update = Signal(bool)

    def __init__(self, ctx: ZContext):
        super().__init__()
        self.ctx = ctx


class CheckCodeRunner(CheckRunnerBase):
    def run(self):
        is_latest, msg = self.ctx.git_service.is_current_branch_latest()
        if msg not in ["与远程分支不一致", "获取远程代码失败"]:
            self.need_update.emit(not is_latest)


class CheckVenvRunner(CheckRunnerBase):
    def run(self):
        last = self.ctx.env_config.requirement_time
        if last != self.ctx.git_service.get_requirement_time():
            self.need_update.emit(True)


class CheckModelRunner(CheckRunnerBase):
    def run(self):
        self.need_update.emit(self.ctx.yolo_config.using_old_model())

class HomeInterface(VerticalScrollInterface):
    """主页界面"""

    def __init__(self, ctx: ZContext, parent=None):

        # 创建垂直布局的主窗口部件
        # index.png 来自 C:\Users\YOUR_NAME\AppData\Roaming\miHoYo\HYP\1_1\fedata\Cache\Cache_Data
        # 对此路径下文件增加后缀名.png后可见
        v_widget = Banner(os.path.join(
            os_utils.get_path_under_work_dir('assets', 'ui'),
            'index.png'
        ))
        v_widget.set_percentage_size(0.8, 0.5)  # 设置 Banner 大小为窗口的 80% 宽度和 50% 高度

        v_layout = QVBoxLayout(v_widget)
        v_layout.setContentsMargins(0, 0, 0, 15)
        v_layout.setSpacing(5)
        v_layout.setAlignment(Qt.AlignTop)

        # 空白占位符
        v_layout.addItem(QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))

        # 顶部部分 (按钮组)
        h1_layout = QHBoxLayout()
        h1_layout.setAlignment(Qt.AlignTop)

        # 左边留白区域
        h1_layout.addStretch()

        # 按钮组
        buttonGroup = ButtonGroup()
        buttonGroup.setMaximumHeight(320)
        h1_layout.addWidget(buttonGroup)

        # 空白占位符
        h1_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Minimum))

        # 将顶部水平布局添加到垂直布局
        v_layout.addLayout(h1_layout)

        # 中间留白区域
        v_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Fixed, QSizePolicy.Minimum))
        v_layout.addStretch()

        # 底部部分 (公告卡片 + 启动按钮)
        h2_layout = QHBoxLayout()
        h2_layout.setAlignment(Qt.AlignTop)

        # 左边留白区域
        h2_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Minimum))

        # 公告卡片
        noticeCard = NoticeCard()
        h2_layout.addWidget(noticeCard)

        h2_layout.addStretch()

        # 启动游戏按钮布局
        gameButton = PrimaryPushButton("启动游戏")
        gameButton.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        gameButton.setFixedSize(160, 48)
        gameButton.clicked.connect(self.start_game)

        v1_layout = QVBoxLayout()
        v1_layout.addWidget(gameButton, alignment=Qt.AlignmentFlag.AlignBottom)

        h2_layout.addLayout(v1_layout)

        # 空白占位符
        v_layout.addItem(QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))

        # self.setLayout(v_layout)

        # 将底部水平布局添加到垂直布局
        v_layout.addLayout(h2_layout)

        # 初始化父类
        super().__init__(
            parent=parent,
            content_widget=v_widget,
            object_name="home_interface",
            nav_text_cn="仪表盘",
            nav_icon=FluentIcon.HOME,
        )

        # 应用样式
        PhosStyleSheet.GAME_BUTTON.apply(gameButton)
        PhosStyleSheet.NOTICE_CARD.apply(noticeCard)

        self.ctx = ctx
        self._init_check_runners()

    def _init_check_runners(self):
        """初始化检查更新的线程"""
        self._check_code_runner = CheckCodeRunner(self.ctx)
        self._check_code_runner.need_update.connect(self._need_to_update_code)
        self._check_venv_runner = CheckVenvRunner(self.ctx)
        self._check_venv_runner.need_update.connect(self._need_to_update_venv)
        self._check_model_runner = CheckModelRunner(self.ctx)
        self._check_model_runner.need_update.connect(self._need_to_update_model)

    def on_interface_shown(self) -> None:
        """界面显示时启动检查更新的线程"""
        super().on_interface_shown()
        self._check_code_runner.start()
        self._check_venv_runner.start()
        self._check_model_runner.start()

    def _need_to_update_code(self, with_new: bool):
        if not with_new:
            return
        self._show_info_bar("有新版本啦", "到代码同步里更新吧~")
        if self.ctx.env_config.auto_update:
            result, msg = self.ctx.git_service.fetch_latest_code()
            if result:
                self._show_dialog_after_code_updated()

    def _need_to_update_venv(self, with_new: bool):
        if with_new:
            self._show_info_bar("运行依赖更新", "到安装器更新吧~")

    def _need_to_update_model(self, with_new: bool):
        if with_new:
            self._show_info_bar("有新模型啦", "到[设置-模型选择]更新吧~", 5000)

    def _show_info_bar(self, title: str, content: str, duration: int = 20000):
        """显示信息条"""
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self,
        ).setCustomBackgroundColor("white", "#202020")

    def _show_dialog_after_code_updated(self):
        """显示代码更新后的对话框"""
        dialog = Dialog("更新提醒", "代码已自动更新，是否重启?", self)
        dialog.setTitleBarVisible(False)
        dialog.yesButton.setText("重启")
        dialog.cancelButton.setText("取消")
        if dialog.exec():
            from one_dragon.utils import app_utils

            app_utils.start_one_dragon(restart=True)

    def start_game(self):
        # 弹出窗口显示 "游戏启动中"
        self.msg_box = GameDialog("少女祈祷中………", parent=self)
        self.msg_box.show()

        # 创建一个线程处理游戏启动
        self.gameThread = GameStartThread(self.ctx)
        self.gameThread.game_started.connect(self.on_game_started)
        self.gameThread.game_failed.connect(self.on_game_failed)
        self.gameThread.start()

    def on_game_started(self):
        self.msg_box.close_dialog()

    def on_game_failed(self):
        self.msg_box.close_dialog()
        log.error("启动游戏失败")


class GameStartThread(QThread):
    # 自定义信号，用于更新主窗口 UI
    game_started = Signal()
    game_failed = Signal(str)

    def __init__(self, ctx: ZContext):
        super().__init__()
        self.ctx = ctx

    def run(self):
        try:
            ctx = ZContext()
            ctx.init_by_config()
            ctx.start_running()
            ctx.ocr.init_model()
            operation = LauncherGame(ctx)
            result = operation.execute()
            if result.success:
                self.game_started.emit()
            else:
                self.game_failed.emit()
        except Exception as e:
            log.error("启动游戏失败: %s")
            self.game_failed.emit(str(e))


class LauncherGame(Operation):
    def __init__(
        self,
        ctx: ZContext,
        node_max_retry_times: int = 3,
        op_name: str = gt("等待游戏打开", "ui"),
        timeout_seconds: float = -1,
        op_callback: Optional[Callable[[OperationResult], None]] = None,
        need_check_game_win: bool = True,
    ):
        self.ctx: ZContext = ctx
        op_to_enter_game = OpenGame(ctx)
        Operation.__init__(
            self,
            ctx=ctx,
            node_max_retry_times=node_max_retry_times,
            op_name=op_name,
            timeout_seconds=timeout_seconds,
            op_callback=op_callback,
            need_check_game_win=need_check_game_win,
            op_to_enter_game=op_to_enter_game,
        )

    @operation_node(name="等待游戏打开", node_max_retry_times=60, is_start_node=True)
    def wait_game(self) -> OperationRoundResult:
        self.ctx.controller.game_win.init_win()
        if self.ctx.controller.is_game_window_ready:
            self.ctx.controller.active_window()
            return self.round_success()
        else:
            return self.round_retry(wait=1)
