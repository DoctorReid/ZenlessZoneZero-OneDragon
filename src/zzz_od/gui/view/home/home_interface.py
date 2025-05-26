import os
import requests
import tempfile
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

from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from one_dragon_qt.services.styles_manager import OdQtStyleSheet
from one_dragon_qt.widgets.banner import Banner
from one_dragon_qt.widgets.icon_button import IconButton
from one_dragon_qt.widgets.notice_card import NoticeCard
from one_dragon_qt.widgets.vertical_scroll_interface import (
    VerticalScrollInterface,
)
from zzz_od.context.zzz_context import ZContext


class ButtonGroup(SimpleCardWidget):
    """显示主页和 GitHub 按钮的竖直按钮组"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setFixedSize(56, 180)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

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

        # 创建 文档 按钮
        doc_button = IconButton(
            FluentIcon.LIBRARY.icon(color=QColor("#fff")),
            tip_title="自助排障文档",
            tip_content="点击打开自助排障文档,好孩子都能看懂",
            isTooltip=True,
        )
        doc_button.setIconSize(QSize(32, 32))
        doc_button.clicked.connect(self.open_doc)
        layout.addWidget(doc_button)

        # 创建 Q群 按钮
        doc_button = IconButton(
            FluentIcon.CHAT.icon(color=QColor("#fff")),
            tip_title="官方社群",
            tip_content="加入官方群聊【绝区零&一条龙交流群】",
            isTooltip=True,
        )
        doc_button.setIconSize(QSize(32, 32))
        doc_button.clicked.connect(self.open_chat)
        layout.addWidget(doc_button)

        # 创建 官方店铺 按钮 (当然没有)
        doc_button = IconButton(
            FluentIcon.SHOPPING_CART.icon(color=QColor("#fff")),
            tip_title="官方店铺",
            tip_content="当然没有官方店铺,本软件完全免费, 速速加入官方社群!",
            isTooltip=True,
        )
        doc_button.setIconSize(QSize(32, 32))
        doc_button.clicked.connect(self.open_sales)
        layout.addWidget(doc_button)

        # 未完工区域, 暂时隐藏
        # # 添加一个可伸缩的空白区域
        # layout.addStretch()

        # # 创建 同步 按钮
        # sync_button = IconButton(
        #     FluentIcon.SYNC.icon(color=QColor("#fff")), tip_title="未完工", tip_content="开发中", isTooltip=True
        # )
        # sync_button.setIconSize(QSize(32, 32))
        # layout.addWidget(sync_button)

    def _normalBackgroundColor(self):
        return QColor(0, 0, 0, 96)

    def open_home(self):
        """打开主页链接"""
        QDesktopServices.openUrl(QUrl("https://onedragon-anything.github.io/zzz/zh/home.html"))

    def open_github(self):
        """打开 GitHub 链接"""
        QDesktopServices.openUrl(
            QUrl("https://github.com/DoctorReid/ZenlessZoneZero-OneDragon")
        )

    def open_chat(self):
        """打开 Q群 链接"""
        QDesktopServices.openUrl(QUrl("https://qm.qq.com/q/N5iEy8sTu0"))

    def open_doc(self):
        """打开 巡夜的金山文档 链接"""
        QDesktopServices.openUrl(QUrl("https://kdocs.cn/l/cbSJUUNotJ3Z"))

    def open_sales(self):
        """其实还是打开 Q群 链接"""
        QDesktopServices.openUrl(QUrl("https://qm.qq.com/q/N5iEy8sTu0"))

class CheckRunnerBase(QThread):
    """检查更新的基础线程类"""

    need_update = Signal(bool)

    def __init__(self, ctx: ZContext):
        super().__init__()
        self.ctx = ctx

class CheckCodeRunner(CheckRunnerBase):
    def run(self):
        is_latest, msg = self.ctx.git_service.is_current_branch_latest()
        if msg in ["与远程分支不一致"]:
            self.need_update.emit(True)
        if msg not in ["获取远程代码失败"]:
            self.need_update.emit(not is_latest)

class CheckVenvRunner(CheckRunnerBase):
    def run(self):
        last = self.ctx.env_config.requirement_time
        if last != self.ctx.git_service.get_requirement_time():
            self.need_update.emit(True)


class CheckModelRunner(CheckRunnerBase):
    def run(self):
        self.need_update.emit(self.ctx.yolo_config.using_old_model())

from PySide6.QtCore import QObject, Signal

class BannerDownloader(QThread):
    banner_downloaded = Signal(str)

    def __init__(self, save_path, parent=None):
        super().__init__(parent)
        self.save_path = save_path
        self.url = "https://hyp-api.mihoyo.com/hyp/hyp-connect/api/getAllGameBasicInfo?launcher_id=jGHBHlcOq1&language=zh-cn"

    def run(self):
        try:
            resp = requests.get(self.url, timeout=5, verify=False)
            data = resp.json()
            for game in data.get("data", {}).get("game_info_list", []):
                if game.get("game", {}).get("biz") == "nap_cn":
                    backgrounds = game.get("backgrounds", [])
                    if backgrounds:
                        img_url = backgrounds[0]["background"]["url"]
                        img_resp = requests.get(img_url, timeout=5, verify=False)
                        if img_resp.status_code == 200:
                            with open(self.save_path, "wb") as f:
                                f.write(img_resp.content)
                            self.banner_downloaded.emit(self.save_path)
                        break
        except Exception as e:
            log(f"主页动态背景异步获取失败: {e}")

class HomeInterface(VerticalScrollInterface):
    """主页界面"""

    # 添加信号
    banner_settings_changed = Signal()

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        self.main_window = parent

        # 主页背景优先级：自定义 > 远端 > index.png
        use_custom_banner = self.ctx.custom_config.banner  # 自定义主页背景开关
        use_remote_banner = self.ctx.custom_config.use_remote_banner  # 远端主页背景开关
        custom_banner_path = os.path.join(os_utils.get_path_under_work_dir('custom', 'assets', 'ui'), 'banner')
        remote_banner_path = os.path.join(os_utils.get_path_under_work_dir('assets', 'ui'), 'remote_banner.webp')
        index_banner_path = os.path.join(os_utils.get_path_under_work_dir('assets', 'ui'), 'index.png')

        if use_custom_banner and os.path.isfile(custom_banner_path):
            banner_path = custom_banner_path
        elif use_remote_banner and os.path.isfile(remote_banner_path):
            banner_path = remote_banner_path
        else:
            banner_path = index_banner_path
        self._banner_path = banner_path
        self._banner_widget = Banner(banner_path)
        self._banner_widget.set_percentage_size(0.8, 0.5)

        # 只在开关打开时才异步获取远端
        self._remote_banner_path = remote_banner_path
        if use_remote_banner:
            self._banner_downloader = BannerDownloader(self._remote_banner_path)
            self._banner_downloader.banner_downloaded.connect(self._on_banner_downloaded)
            self._banner_downloader.start()

        v_layout = QVBoxLayout(self._banner_widget)
        v_layout.setContentsMargins(0, 0, 0, 15)
        v_layout.setSpacing(5)
        v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 空白占位符
        v_layout.addItem(QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # 顶部部分 (按钮组)
        h1_layout = QHBoxLayout()
        h1_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 左边留白区域
        h1_layout.addStretch()

        # 按钮组
        buttonGroup = ButtonGroup()
        buttonGroup.setMaximumHeight(320)
        h1_layout.addWidget(buttonGroup)

        # 空白占位符
        h1_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # 将顶部水平布局添加到垂直布局
        v_layout.addLayout(h1_layout)

        # 中间留白区域
        v_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        v_layout.addStretch()

        # 底部部分 (公告卡片 + 启动按钮)
        h2_layout = QHBoxLayout()
        h2_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 左边留白区域
        h2_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # 公告卡片
        noticeCard = NoticeCard()
        h2_layout.addWidget(noticeCard)

        h2_layout.addStretch()

        # 启动游戏按钮布局
        gameButton = PrimaryPushButton(text="启动一条龙🚀")
        gameButton.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        gameButton.setFixedSize(160, 48)
        gameButton.clicked.connect(self._on_start_game)

        v1_layout = QVBoxLayout()
        v1_layout.addWidget(gameButton, alignment=Qt.AlignmentFlag.AlignBottom)

        h2_layout.addLayout(v1_layout)

        # 空白占位符
        h2_layout.addItem(QSpacerItem(25, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # 将底部水平布局添加到垂直布局
        v_layout.addLayout(h2_layout)

        # 初始化父类
        super().__init__(
            parent=parent,
            content_widget=self._banner_widget,
            object_name="home_interface",
            nav_text_cn="仪表盘",
            nav_icon=FluentIcon.HOME,
        )

        # 连接信号
        self.banner_settings_changed.connect(self._on_banner_settings_changed)
        # 应用样式
        OdQtStyleSheet.GAME_BUTTON.apply(gameButton)
        OdQtStyleSheet.NOTICE_CARD.apply(noticeCard)

        self.ctx = ctx
        self._init_check_runners()

    def _on_banner_downloaded(self, path):
        # 刷新 Banner 显示为新图片
        self._banner_widget.banner_image = self._banner_widget.load_banner_image(path)
        self._banner_widget.update_scaled_image()
        self._banner_widget.update()

    def _init_check_runners(self):
        """初始化检查更新的线程"""
        self._check_code_runner = CheckCodeRunner(self.ctx)
        self._check_code_runner.need_update.connect(self._need_to_update_code)
        self._check_venv_runner = CheckVenvRunner(self.ctx)
        self._check_venv_runner.need_update.connect(self._need_to_update_venv)
        self._check_model_runner = CheckModelRunner(self.ctx)
        self._check_model_runner.need_update.connect(self._need_to_update_model)

    def _on_banner_settings_changed(self) -> None:
        """
        当横幅设置改变时触发
        """
        log.info("[HomeInterface] _on_banner_settings_changed called")
        self.refresh_banner(show_notification=True)

    def on_interface_shown(self) -> None:
        """界面显示时启动检查更新的线程"""
        super().on_interface_shown()
        self._check_code_runner.start()
        self._check_venv_runner.start()
        self._check_model_runner.start()
        
        # 检查并更新背景，但不显示提示
        self.refresh_banner(show_notification=False)

    def _need_to_update_code(self, with_new: bool):
        if not with_new:
            self._show_info_bar("代码已是最新版本", "Enjoy it & have fun!")
            return
        else :
            self._show_info_bar("有新版本啦", "稍安勿躁~")
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
            parent=self.main_window,  # 修改这里
        ).setCustomBackgroundColor("white", "#202020")

    def _show_dialog_after_code_updated(self):
        """显示代码更新后的对话框"""
        dialog = Dialog("更新提醒", "如果你仍然能看到此弹窗，请前往 GitHub Release 更新启动器", self)
        dialog.setTitleBarVisible(False)
        dialog.yesButton.setText("重启")
        dialog.cancelButton.setText("取消")
        if dialog.exec():
            from one_dragon.utils import app_utils
            app_utils.start_one_dragon(restart=True)

    def _on_start_game(self):
        """启动一条龙按钮点击事件处理"""

        # app.py中一条龙界面为第三个添加的
        self.ctx.home_start_button_pressed = True
        one_dragon_interface = self.main_window.stackedWidget.widget(2)
        self.main_window.switchTo(one_dragon_interface)

    def refresh_banner(self, show_notification: bool = False) -> None:
        """
        刷新横幅显示
        :param show_notification: 是否显示提示
        :return:
        """
        log.info(f"[HomeInterface] refresh_banner called. use_remote_banner={self.ctx.custom_config.use_remote_banner}, use_custom_banner={self.ctx.custom_config.banner}")
        # 获取背景图片路径
        custom_banner_path = os.path.join(
            os_utils.get_path_under_work_dir('custom', 'assets', 'ui'),
            'banner')
        remote_banner_path = os.path.join(
            os_utils.get_path_under_work_dir('assets', 'ui'),
            'remote_banner.webp')
        index_banner_path = os.path.join(
            os_utils.get_path_under_work_dir('assets', 'ui'),
            'index.png')
        log.info(f"[HomeInterface] custom_banner_path={custom_banner_path}, exists={os.path.exists(custom_banner_path)}")
        log.info(f"[HomeInterface] remote_banner_path={remote_banner_path}, exists={os.path.exists(remote_banner_path)}")
        log.info(f"[HomeInterface] index_banner_path={index_banner_path}, exists={os.path.exists(index_banner_path)}")

        # 根据设置选择背景图片
        if self.ctx.custom_config.use_remote_banner and os.path.exists(remote_banner_path):
            banner_path = remote_banner_path
        elif self.ctx.custom_config.banner and os.path.exists(custom_banner_path):
            banner_path = custom_banner_path
        else:
            banner_path = index_banner_path
        log.info(f"[HomeInterface] set banner_path={banner_path}")

        # 更新背景图片
        self._banner_widget.set_banner_image(banner_path)

        if show_notification:
            self._show_info_bar(title=gt("背景已更新", "ui"), content=gt("新的背景已成功应用", "ui"), duration=3000)
