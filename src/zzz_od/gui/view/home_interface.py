import os
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QFont, QColor, QLinearGradient, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSpacerItem, QSizePolicy
from qfluentwidgets import FluentIcon, InfoBar, InfoBarPosition, Dialog, ComboBox

from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.link_card import LinkCardView
from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext

# 常量定义
CORNER_RADIUS = 20  # 圆角半径
TEXT_SIZE = 36  # 文字大小
TEXT_OFFSET = 36  # 文字距离右边的偏移量


class BannerWidget(QWidget):
    """展示带有圆角和自适应宽度和高度的横幅小部件"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(320)  # 初始设置固定高度

        self.banner_image = self.load_banner_image()  # 加载横幅图片
        self.aspect_ratio = self.banner_image.width() / self.banner_image.height()  # 计算图片的宽高比

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(0)  # 设置布局的间距
        self.vBoxLayout.setContentsMargins(0, 20, 0, 0)  # 设置布局的边距
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # 设置布局对齐方式

        self.linkCardView = LinkCardView(self)
        self.vBoxLayout.addWidget(self.linkCardView, 1, Qt.AlignmentFlag.AlignBottom)  # 添加链接卡片视图，垂直方向上对齐底部

        # 添加间隔项
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.vBoxLayout.addItem(spacer)

        # 向链接卡片视图中添加一个卡片
        self.linkCardView.addCard(
            FluentIcon.GITHUB,
            gt('仓库地址', 'ui'),
            self.tr('如果本项目有帮助到您~\n不妨给项目点一个Star⭐'),
            "https://github.com/DoctorReid/ZenlessZoneZero-OneDragon"
        )

    def load_banner_image(self):
        """加载横幅图片，如果图片文件不存在则创建一个渐变的备用图片"""
        image_path = os.path.join(os_utils.get_path_under_work_dir('assets', 'ui'), '1.png')
        if os.path.isfile(image_path):
            return QPixmap(image_path)
        return self.create_fallback_image()

    def create_fallback_image(self):
        """创建一个渐变的备用图片，当横幅图片文件不存在时使用"""
        fallback_image = QPixmap(800, 320)  # 设置一个默认的大小，之后会自动调整
        fallback_image.fill(Qt.transparent)  # 填充透明背景
        painter = QPainter(fallback_image)
        gradient = QLinearGradient(0, 0, 0, 320)
        gradient.setColorAt(0, QColor(0, 0, 0, 0))  # 渐变的开始颜色为透明
        gradient.setColorAt(1, QColor(0, 0, 0, 127))  # 渐变的结束颜色为半透明黑色
        painter.fillRect(fallback_image.rect(), gradient)  # 用渐变填充图片
        painter.end()
        return fallback_image

    def resizeEvent(self, event):
        """窗口大小调整事件，重新计算横幅高度并更新图片"""
        super().resizeEvent(event)
        new_width = self.width()
        new_height = int(new_width / self.aspect_ratio)
        self.setFixedHeight(new_height)

        # 重新设置横幅图片的大小
        self.banner_image = self.banner_image.scaled(
            new_width, new_height, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
        )
        self.update()  # 触发重绘
        
        # 强制更新子布局和组件
        self.vBoxLayout.invalidate()
        self.linkCardView.updateGeometry()
        self.updateGeometry()

    def paintEvent(self, event):
        """绘制事件，负责绘制横幅背景和文字"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.SmoothPixmapTransform | QPainter.RenderHint.Antialiasing)  # 设置平滑缩放和抗锯齿

        # 获取小部件的宽度和高度
        w, h = self.width(), self.height()

        # 绘制横幅图片
        banner_pixmap = self.banner_image.copy(
            (self.banner_image.width() - w) // 2, (self.banner_image.height() - h) // 2, w, h
        )

        # 创建一个圆角矩形路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, CORNER_RADIUS, CORNER_RADIUS)

        # 使用圆角矩形路径剪切绘制区域，并绘制横幅图片
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, banner_pixmap)

        # 定义文本大小和间距
        TEXT_SIZE = 24
        TEXT_OFFSET = 50
        BACKGROUND_PADDING = 10  # 矩形与文字之间的间距
        ROUNDED_RADIUS = 10  # 圆角半径

        # 准备绘制主标题文字
        font = QFont("Microsoft YaHei", TEXT_SIZE, QFont.Weight.Bold)
        painter.setFont(font)
        text = "OneDragon"
        text_rect = painter.fontMetrics().boundingRect(text)
        text_rect.moveRight(w-TEXT_OFFSET)  # 将文字稍微向右移动
        text_rect.moveTop(TEXT_OFFSET)  # 将文字稍微向右移动

        # 计算背景矩形的位置和大小
        background_rect = text_rect.adjusted(-15, -10, 15, 40)
        painter.setPen(Qt.NoPen)  # 不绘制边框
        painter.setBrush(QBrush(QColor(0, 0, 0, 127)))  # 半透明黑色背景
        painter.drawRoundedRect(background_rect, ROUNDED_RADIUS, ROUNDED_RADIUS)

        # 绘制主标题文字
        painter.setPen(Qt.white)
        painter.drawText(text_rect, text)

        # 准备绘制副标题文字
        small_font = QFont("Microsoft YaHei", 16, QFont.Weight.Bold)
        painter.setFont(small_font)
        small_text = "绝区零一条龙小助手 "
        small_text_rect = painter.fontMetrics().boundingRect(small_text)

        # 直接定位到主标题的下方
        small_text_rect.moveLeft(text_rect.left())  # 与主标题左对齐
        small_text_rect.moveTop(text_rect.bottom() + 2)  # 放置在主标题下方，间距为2像素

        # 绘制副标题文字
        painter.setPen(Qt.white)
        painter.drawText(small_text_rect, small_text)

        painter.end()


class CheckCodeRunner(QThread):
    need_update = Signal(bool)

    def __init__(self, ctx: ZContext):
        super().__init__()
        self.ctx = ctx

    def run(self):
        """
        运行 最后发送结束信号
        :return:
        """
        is_latest, msg = self.ctx.git_service.is_current_branch_latest()
        if msg not in ['与远程分支不一致', '获取远程代码失败']:
            self.need_update.emit(not is_latest)
        # self.need_update.emit(True)  # 调试用


class CheckModelRunner(QThread):
    need_update = Signal(bool)

    def __init__(self, ctx: ZContext):
        super().__init__()
        self.ctx = ctx

    def run(self):
        """
        运行 最后发送结束信号
        :return:
        """
        self.need_update.emit(self.ctx.yolo_config.using_old_model())


class HomeInterface(VerticalScrollInterface):
    """主页界面"""

    def __init__(self, ctx: ZContext, parent=None):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        content_layout.setContentsMargins(0, 0, 0, 36)  # 设置内容的边距
        content_layout.setSpacing(40)  # 设置内容的间距
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # 设置内容对齐方式

        # 创建横幅小部件并添加到布局中
        banner = BannerWidget()
        content_layout.addWidget(banner)
        
        # 初始化父类并设置导航相关属性
        super().__init__(
            ctx=ctx, parent=parent,
            content_widget=content_widget, object_name='home_interface',
            nav_text_cn='主页', nav_icon=FluentIcon.HOME
        )

        self._check_code_runner = CheckCodeRunner(self.ctx)
        self._check_code_runner.need_update.connect(self._need_to_update_code)

        self._check_model_runner = CheckModelRunner(self.ctx)
        self._check_model_runner.need_update.connect(self._need_to_update_model)

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)
        self._check_code_runner.start()
        self._check_model_runner.start()

    def _need_to_update_code(self, with_new: bool):
        if not with_new:
            return
        w = InfoBar.success(
            title='有新版本啦',
            content="到代码同步里更新吧~",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=20000,
            parent=self
        )
        w.setCustomBackgroundColor('white', '#202020')
        if self.ctx.env_config.auto_update:
            result, msg = self.ctx.git_service.fetch_latest_code()
            # result = True  # 调试用
            if result:
                self._show_dialog_after_code_updated()

    def _show_dialog_after_code_updated(self):
        title = '更新提醒'
        content = "代码已自动更新，是否重启?"
        w = Dialog(title, content, self)
        w.setTitleBarVisible(False)
        w.yesButton.setText('重启')
        w.cancelButton.setText('取消')
        if w.exec():
            from one_dragon.utils import app_utils
            app_utils.start_one_dragon(restart=True)

    def _need_to_update_model(self, with_new: bool):
        if not with_new:
            return
        w = InfoBar.success(
            title='有新模型啦',
            content="到[设置-模型选择]更新吧~",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000,
            parent=self
        )
        w.setCustomBackgroundColor('white', '#202020')
