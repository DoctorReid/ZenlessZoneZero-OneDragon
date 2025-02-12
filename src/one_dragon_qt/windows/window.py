import sys
from PySide6.QtCore import (
    Qt,
    Signal,
    QRect,
    QRectF,
    QUrl
)
from PySide6.QtGui import QIcon, QPainter, QColor, QFont, QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QHBoxLayout,
    QPushButton, QApplication,QAbstractScrollArea
)
from qfluentwidgets import (
    FluentStyleSheet,
    isDarkTheme,
    FluentIcon as FIF,
    setFont,
    SplitTitleBar,
    NavigationBarPushButton,
    MSFluentWindow,
    SingleDirectionScrollArea,
    NavigationBar,
    qrouter,
    FluentIconBase,
    NavigationItemPosition, InfoBar, InfoBarPosition,
)
from qfluentwidgets.common.animation import BackgroundAnimationWidget
from qfluentwidgets.common.config import qconfig
from qfluentwidgets.components.widgets.frameless_window import FramelessWindow
from qfluentwidgets.window.stacked_widget import StackedWidget
from typing import Union


# 伪装的父类,用于替换原本的FluentWindowBase初始化
class PhosFluentWindowBase(BackgroundAnimationWidget, FramelessWindow):
    """Fluent window base class"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)


# 主窗口类，继承自 MSFluentWindow，重绘部分功能
class PhosWindow(MSFluentWindow, PhosFluentWindowBase):

    def __init__(self, parent=None):

        # 初始化
        self._isAeroEnabled = False

        # 调用原始父类执行初始化
        self._isMicaEnabled = False
        self._lightBackgroundColor = QColor(240, 244, 249)
        self._darkBackgroundColor = QColor(32, 32, 32)
        PhosFluentWindowBase.__init__(self, parent=parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.stackedWidget = PhosStackedWidget(self)
        self.navigationInterface = None

        # initialize layout
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        FluentStyleSheet.FLUENT_WINDOW.apply(self.stackedWidget)

        # enable mica effect on win11
        self.setMicaEffectEnabled(True)

        # show system title bar buttons on macOS
        if sys.platform == "darwin":
            self.setSystemTitleBarButtonVisible(True)

        qconfig.themeChangedFinished.connect(self._onThemeChangedFinished)

        # 设置自定义标题栏和导航栏
        self.setTitleBar(PhosTitleBar(self))
        self.navigationInterface = OneDragonNavigationBar(self)

        self.areaWidget = QWidget()
        self.areaLayout = QHBoxLayout(self.areaWidget)

        # 设置布局
        self.hBoxLayout.addWidget(self.navigationInterface)

        self.hBoxLayout.addWidget(self.areaWidget)
        self.hBoxLayout.setStretchFactor(self.areaWidget, 1)

        self.areaLayout.addWidget(self.stackedWidget)
        self.areaLayout.setContentsMargins(0, 32, 0, 0)

        self.areaWidget.setObjectName("areaWidget")

        self.titleBar.raise_()
        self.titleBar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

    # 设置 Aero 磨砂效果
    def setAeroEffectEnabled(self, isEnabled: bool):
        if sys.platform != "win32":  # 仅在 Windows 平台启用
            return

        self._isAeroEnabled = isEnabled

        if isEnabled:
            # 启用 Aero 效果
            self.windowEffect.setAeroEffect(int(self.winId()))
        else:
            # 移除背景效果
            self.windowEffect.removeBackgroundEffect(self.winId())

        self.setBackgroundColor(self._normalBackgroundColor())  # 设置背景颜色

    # 判断是否启用了 Aero 效果
    def isAeroEffectEnabled(self):
        return self._isAeroEnabled

    # 获取正常的背景颜色
    def _normalBackgroundColor(self):
        if not self.isAeroEffectEnabled():
            # 根据当前主题设置背景颜色
            return (
                self._darkBackgroundColor
                if isDarkTheme()
                else self._lightBackgroundColor
            )

        # 透明背景
        return QColor(0, 0, 0, 0)

    # 主题改变时的回调函数
    def _onThemeChangedFinished(self):
        if self.isAeroEffectEnabled():
            # 重新设置 Aero 效果
            self.windowEffect.setAeroEffect(self.winId(), isDarkTheme())

    # 标题位置
    def resizeEvent(self, e):
        self.titleBar.move(self.navigationInterface.width() + 16, 0)
        self.titleBar.resize(
            self.width() - self.navigationInterface.width() - 16, self.titleBar.height()
        )


# 自定义导航栏类，继承自 NavigationBar
class OneDragonNavigationBar(NavigationBar):

    def __init__(self, parent=None):
        super(NavigationBar, self).__init__(parent)

        # 初始化滚动区域和布局
        self.scrollArea = SingleDirectionScrollArea(self)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self)
        self.topLayout = QVBoxLayout()
        self.bottomLayout = QVBoxLayout()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)

        self.items = {}  # 存储导航项
        self.history = qrouter  # 路由历史管理

        self.__initWidget()  # 初始化界面

    # 初始化窗口属性
    def __initWidget(self):
        self.resize(48, self.height())
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.window().installEventFilter(self)  # 安装事件过滤器

        # 设置滚动条样式
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)

        self.scrollWidget.setObjectName("scrollWidget")
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self)
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self.scrollWidget)

        # 初始化布局
        self.__initLayout()  

    # 初始化布局
    def __initLayout(self):
        # 设置布局边距和间距
        self.vBoxLayout.setContentsMargins(0, 5, 0, 5)
        self.topLayout.setContentsMargins(4, 0, 4, 0)
        self.bottomLayout.setContentsMargins(4, 0, 4, 0)
        self.scrollLayout.setContentsMargins(4, 0, 4, 0)
        self.vBoxLayout.setSpacing(4)
        self.topLayout.setSpacing(4)
        self.bottomLayout.setSpacing(4)
        self.scrollLayout.setSpacing(4)

        # 添加布局到主布局
        self.vBoxLayout.addLayout(self.topLayout, 0)
        self.vBoxLayout.addWidget(self.scrollArea)
        self.vBoxLayout.addLayout(self.bottomLayout, 0)

        # 对齐方式
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.topLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.bottomLayout.setAlignment(Qt.AlignmentFlag.AlignBottom)

    # 插入导航项
    def insertItem(
        self,
        index: int,
        routeKey: str,
        icon: Union[str, QIcon, FluentIconBase],
        text: str,
        onClick=None,
        selectable=True,
        selectedIcon=None,
        position=NavigationItemPosition.TOP,
    ):
        if routeKey in self.items:
            return

        # 创建自定义导航按钮
        w = PhosNavigationBarPushButton(icon, text, selectable, selectedIcon, self)
        self.insertWidget(index, routeKey, w, onClick, position)
        return w

    def _onWidgetClicked(self):
        widget = self.sender()
        if widget.isSelectable:
            # 路由切换逻辑
            route_key = widget.property("routeKey")
            self.setCurrentItem(route_key)

# 自定义导航按钮类
class PhosNavigationBarPushButton(NavigationBarPushButton):
    def __init__(
        self,
        icon: Union[str, QIcon, FIF],
        text: str,
        isSelectable: bool,
        selectedIcon=None,
        parent=None
    ):
        super(NavigationBarPushButton, self).__init__(icon, text, isSelectable, parent)

        #几何参数
        self.setFixedSize(64, 56)
        self.icon_rect = QRectF(22, 13, 20, 20)
        self.text_rect = QRect(0, 32, 64, 26)

        #主题参数
        self._theme_colors = {
            'dark_icon': "#b2b2b2",
            'light_icon': "#5c6e93",
            'selected_icon': "#ffffff",
            'background_dark': 255,
            'background_light': 0
        }

        self._selectedIcon = selectedIcon or icon

        #设置样式
        setFont(self, 12, weight=QFont.Weight.ExtraBold)
        self._isSelectedTextVisible = True

    def paintEvent(self, e):
        painter = QPainter(self)
        self._configure_painter(painter)
        self._draw_background(painter)
        self._draw_icon(painter)
        self._draw_text(painter)

    def _configure_painter(self, painter):
        """配置参数"""
        painter.setRenderHints(
            QPainter.Antialiasing |
            QPainter.TextAntialiasing |
            QPainter.SmoothPixmapTransform
        )
        painter.setPen(Qt.NoPen)

    def _draw_background(self, painter):
        """背景绘制"""
        color = self._get_background_color()
        painter.setBrush(color)
        painter.drawRoundedRect(self.rect().adjusted(4, 0, -4, 0), 10, 10)

    def _get_background_color(self):
        """背景颜色"""

        if not self.isSelected:
            if self.isPressed:
                c = self._theme_colors['background_dark' if isDarkTheme()  else 'background_light']
                return QColor(c, c, c, 64)
            elif self.isEnter:
                c = self._theme_colors['background_dark' if isDarkTheme()  else 'background_light']
                return QColor(c, c, c, 32)
            else:
                c = self._theme_colors['background_dark' if isDarkTheme()  else 'background_light']
                return QColor(c, c, c, 0)
        else:
            c = self._theme_colors['background_dark' if isDarkTheme()  else 'background_light']
            return QColor(214, 75, 84, 255)
    

    def _draw_icon(self, painter):
        """图标绘制"""
        fill_color = self._get_icon_color()
        self._selectedIcon.render(painter, self.icon_rect, fill=fill_color)

    def _get_icon_color(self):
        """图标颜色"""
        if self.isSelected:
            if isinstance(self._selectedIcon, FluentIconBase):
                return self._theme_colors['selected_icon']
            return self._theme_colors['light_icon']
        return self._theme_colors['dark_icon' if isDarkTheme()  else 'light_icon']

    def _draw_text(self, painter):
        """文本绘制"""
        if self.isSelected and not self._isSelectedTextVisible:
            return
        
        painter.setPen(self._get_text_color())
        painter.setFont(self.font())
        painter.drawText(self.text_rect, Qt.AlignCenter, self.text())

    def _get_text_color(self):
        """文本颜色"""
        if self.isSelected:
            return QColor(255, 255, 255)
        return QColor(178, 178, 178) if isDarkTheme()  else QColor(92, 110, 147)

    def setSelected(self, isSelected: bool):
        """选中状态切换"""
        if isSelected == self.isSelected:
            return
        
        self.isSelected = isSelected


class PhosTitleBar(SplitTitleBar):
    """One Dragon 自定义标题栏"""

    def __init__(self, parent=None):
        # 调用父类的初始化方法
        super(SplitTitleBar, self).__init__(parent)

        # 设置标题栏的固定高度
        self.setFixedHeight(32)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 10, 0, 0)

        # 添加窗口图标
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(18, 18)
        layout.addWidget(self.iconLabel, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.window().windowIconChanged.connect(self.setIcon)

        # 空白项
        layout.addSpacerItem(
            QSpacerItem(8, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        )

        # 添加窗口标题
        self.titleLabel = QLabel(self)
        layout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.titleLabel.setObjectName("titleLabel")

        self.window().windowTitleChanged.connect(self.setTitle)

        # 扩展空白项
        layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        # 将新创建的布局插入到标题栏的主布局中
        self.hBoxLayout.insertLayout(0, layout)

        Qlayout = QHBoxLayout()
        Qlayout.setContentsMargins(8, 10, 0, 0)

        self.versionButton = QPushButton("ⓘ 代码版本 未知")
        self.versionButton.setObjectName("versionButton")
        self.versionButton.clicked.connect(self.copy_version)
        Qlayout.addWidget(self.versionButton, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.questionButton = QPushButton("ⓘ 问题反馈")
        self.questionButton.setObjectName("questionButton")
        self.questionButton.clicked.connect(self.open_github)
        Qlayout.addWidget(self.questionButton, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # 将新创建的布局插入到标题栏的主布局中
        self.hBoxLayout.insertLayout(2, Qlayout)

        self.issue_url: str = ""
        self.version: str = ""

    def setIcon(self, icon: QIcon):
        self.iconLabel.setPixmap(icon.pixmap(18, 18))

    def setTitle(self, title: str):
        self.titleLabel.setText(title)

    def setVersion(self, version: str) -> None:
        """
        设置版本号 会更新UI
        @param version: 版本号
        @return:
        """
        self.version = version
        self.versionButton.setText(f'ⓘ 代码版本 {version}')

    # 定义打开GitHub网页的函数
    def open_github(self):
        url = QUrl(self.issue_url)
        QDesktopServices.openUrl(url)

    def copy_version(self):
        """
        将版本号复制到粘贴板
        @return:
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(self.version)
        InfoBar.success(
            title='已复制版本号',
            content='',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self.window(),
        ).setCustomBackgroundColor("white", "#202020")



class PhosStackedWidget(StackedWidget):
    """ Stacked widget """

    currentChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def setCurrentWidget(self, widget, popOut=True):
        if isinstance(widget, QAbstractScrollArea):
            widget.verticalScrollBar().setValue(0)
        self.view.setCurrentWidget(widget, duration=0)