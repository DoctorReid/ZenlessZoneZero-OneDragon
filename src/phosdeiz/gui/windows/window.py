import sys

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    Property,
    QRect,
    QRectF,
    QEasingCurve,
    QUrl,
)
from PySide6.QtGui import QIcon, QPainter, QColor, QFont, QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QHBoxLayout,
    QPushButton,
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
    NavigationItemPosition,
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
        self.stackedWidget = StackedWidget(self)
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
        self.setAttribute(Qt.WA_StyledBackground)
        self.window().installEventFilter(self)  # 安装事件过滤器

        # 设置滚动条样式
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)

        self.scrollWidget.setObjectName("scrollWidget")
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self)
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self.scrollWidget)
        self.__initLayout()  # 初始化布局

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
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.topLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.bottomLayout.setAlignment(Qt.AlignBottom)

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

        # 创建自定义按钮
        w = PhosNavigationBarPushButton(icon, text, selectable, selectedIcon, self)
        self.insertWidget(index, routeKey, w, onClick, position)
        return w


# 图标动画类
class IconAnimation(QPropertyAnimation):
    """Icon sliding animation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 0
        self.minOpacity = 100
        self.maxOpacity = 255
        self.setTargetObject(self)
        self.setPropertyName(b"opacity")

    def getOpacity(self):
        return self._opacity

    def setOpacity(self, value: float):
        self._opacity = value
        self.parent().update()  # 更新父对象以重绘

    opacity = Property(float, getOpacity, setOpacity)

    def aniStart(self):
        """slide down"""
        self.setStartValue(self.minOpacity)
        self.setEndValue(self.maxOpacity)
        self.setDuration(400)  # 调整持续时间
        self.setEasingCurve(QEasingCurve.OutCubic)  # 使用缓动函数
        self.start()

    def aniStop(self):
        """slide up"""
        self.setStartValue(20)
        self.setEndValue(0)  # 修改为从最大值到0
        self.setDuration(100)  # 调整持续时间
        self.setEasingCurve(QEasingCurve.InCubic)  # 使用缓动函数
        self.start()


# 自定义导航按钮类
class PhosNavigationBarPushButton(NavigationBarPushButton):
    """Navigation bar push button"""

    def __init__(
        self,
        icon: Union[str, QIcon, FIF],
        text: str,
        isSelectable: bool,
        selectedIcon=None,
        parent=None,
    ):
        super(NavigationBarPushButton, self).__init__(icon, text, isSelectable, parent)
        self.iconAni = IconAnimation(self)  # 图标滑动动画
        self._selectedIcon = selectedIcon
        self._isSelectedTextVisible = True

        self.setFixedSize(64, 58)  # 设置按钮大小
        setFont(self, 12, weight=QFont.Weight.ExtraBold)  # 设置字体大小

    # 绘制事件
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        painter.setPen(Qt.NoPen)

        # 绘制选中按钮样式
        if self.isSelected and not self.isPressed:
            painter.setBrush(
                QColor(214, 75, 84, self.iconAni.opacity)
            )  # 设置选中背景颜色
            painter.drawRoundedRect(self.rect().adjusted(4, 0, -4, 0), 10, 10)
        elif self.isSelected and self.isPressed:
            painter.setBrush(QColor(214, 75, 84, 100))  # 设置选中背景颜色
            painter.drawRoundedRect(self.rect().adjusted(4, 0, -4, 0), 10, 10)
        elif self.isPressed:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 20))  # 设置选中背景颜色
            painter.drawRoundedRect(self.rect().adjusted(4, 0, -4, 0), 10, 10)
        elif self.isEnter:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect().adjusted(4, 0, -4, 0), 10, 10)
        else:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, self.iconAni.opacity))  # 设置默认背景颜色
            painter.drawRoundedRect(self.rect().adjusted(4, 0, -4, 0), 10, 10)

        # 绘制图标
        rect = QRectF(22, 13, 20, 20)
        selectedIcon = self._selectedIcon or self._icon

        if isinstance(selectedIcon, FluentIconBase) and self.isSelected:
            selectedIcon.render(painter, rect, fill="#ffffff")
        elif self.isSelected:
            selectedIcon.render(painter, rect, fill="#5c6e93")
        elif isDarkTheme():
            selectedIcon.render(painter, rect, fill="#b2b2b2")
        else:
            selectedIcon.render(painter, rect, fill="#5c6e93")

        if self.isSelected and not self._isSelectedTextVisible:
            return

        # 绘制文字
        painter.setPen(
            QColor(255, 255, 255)
            if self.isSelected
            else QColor(178, 178, 178) if isDarkTheme() else QColor(92, 110, 147)
        )
        painter.setFont(self.font())
        rect = QRect(0, 32, self.width(), 26)
        painter.drawText(rect, Qt.AlignCenter, self.text())

    def setSelected(self, isSelected: bool):
        if isSelected == self.isSelected:
            return

        self.isSelected = isSelected

        if isSelected:
            self.iconAni.aniStart()
        else:
            self.iconAni.aniStop()


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
        layout.addWidget(self.iconLabel, 0, Qt.AlignLeft | Qt.AlignTop)

        self.window().windowIconChanged.connect(self.setIcon)

        # 空白项
        layout.addSpacerItem(
            QSpacerItem(8, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)
        )

        # 添加窗口标题
        self.titleLabel = QLabel(self)
        layout.addWidget(self.titleLabel, 0, Qt.AlignLeft | Qt.AlignTop)
        self.titleLabel.setObjectName("titleLabel")

        self.window().windowTitleChanged.connect(self.setTitle)

        # 扩展空白项
        layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        # 将新创建的布局插入到标题栏的主布局中
        self.hBoxLayout.insertLayout(0, layout)

        Qlayout = QHBoxLayout()
        Qlayout.setContentsMargins(8, 10, 0, 0)

        # 添加文字按钮
        self.questionButton = QPushButton("ⓘ 问题反馈")
        self.questionButton.setObjectName("questionButton")
        self.questionButton.clicked.connect(self.open_github)
        Qlayout.addWidget(self.questionButton, 0, Qt.AlignLeft | Qt.AlignTop)

        # 将新创建的布局插入到标题栏的主布局中
        self.hBoxLayout.insertLayout(2, Qlayout)

        self.issue_url: str = ""

    def setIcon(self, icon: QIcon):
        self.iconLabel.setPixmap(icon.pixmap(18, 18))

    def setTitle(self, title: str):
        self.titleLabel.setText(title)

    # 定义打开GitHub网页的函数
    def open_github(self):
        url = QUrl(self.issue_url)
        QDesktopServices.openUrl(url)
