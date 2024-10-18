import sys
from PySide6.QtCore import Qt, QPropertyAnimation, Property, QRect, QRectF
from PySide6.QtGui import QIcon, QPainter, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSpacerItem, QSizePolicy
from qfluentwidgets import FluentStyleSheet, drawIcon, isDarkTheme, FluentIcon as FIF, setFont, SplitTitleBar, \
    NavigationBarPushButton, MSFluentWindow, SingleDirectionScrollArea, NavigationBar, qrouter, FluentIconBase, \
    NavigationItemPosition,qconfig
from qfluentwidgets.window.fluent_window import FluentWindowBase
from qfluentwidgets.window.stacked_widget import StackedWidget
from typing import Union

# 主窗口类，继承自 MSFluentWindow，重绘部分功能
class OneDragonWindow(MSFluentWindow):

    def __init__(self, parent=None):
        
        # 初始化
        self._isAeroEnabled = False


        # 调用原始父类执行初始化
        FluentWindowBase.__init__(self, parent=parent)
        
        # 设置自定义标题栏和导航栏
        self.setTitleBar(OdTitleBar(self))
        self.navigationInterface = OneDragonNavigationBar(self)

        self.areaWidget = QWidget()
        self.areaLayout = QHBoxLayout(self.areaWidget)

        # 设置布局
        self.hBoxLayout.addWidget(self.navigationInterface)
        
        self.hBoxLayout.addWidget(self.areaWidget)
        self.hBoxLayout.setStretchFactor(self.areaWidget, 1)

        self.areaLayout.addWidget(self.stackedWidget)
        self.areaLayout.setContentsMargins(0, 32, 0, 0)

        self.areaWidget.setObjectName('areaWidget')

        self.titleBar.raise_()
        self.titleBar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

    # 设置 Aero 磨砂效果
    def setAeroEffectEnabled(self, isEnabled: bool):
        if sys.platform != 'win32':  # 仅在 Windows 平台启用
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
            return self._darkBackgroundColor if isDarkTheme() else self._lightBackgroundColor

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
        self.titleBar.resize(self.width()-self.navigationInterface.width() - 16, self.titleBar.height())


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

        self.scrollWidget.setObjectName('scrollWidget')
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
    def insertItem(self, index: int, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str, onClick=None,
                   selectable=True, selectedIcon=None, position=NavigationItemPosition.TOP):
        if routeKey in self.items:
            return

        # 创建自定义按钮
        w = OdNavigationBarPushButton(icon, text, selectable, selectedIcon, self)
        self.insertWidget(index, routeKey, w, onClick, position)
        return w

# 图标滑动动画类
class IconSlideAnimation(QPropertyAnimation):
    """ Icon sliding animation """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0  # 动画偏移量
        self.maxOffset = 6  # 最大偏移量
        self.setTargetObject(self)  # 设置目标对象
        self.setPropertyName(b"offset")  # 设置动画属性

    # 获取偏移量
    def getOffset(self):
        return self._offset

    # 设置偏移量
    def setOffset(self, value: float):
        self._offset = value
        self.parent().update()  # 更新父对象

    # 向下滑动动画
    def slideDown(self):
        self.setEndValue(self.maxOffset)
        self.setDuration(100)
        self.start()

    # 向上滑动动画
    def slideUp(self):
        self.setEndValue(0)
        self.setDuration(100)
        self.start()

    offset = Property(float, getOffset, setOffset)

# 自定义导航按钮类
class OdNavigationBarPushButton(NavigationBarPushButton):
    """ Navigation bar push button """

    def __init__(self, icon: Union[str, QIcon, FIF], text: str, isSelectable: bool, selectedIcon=None, parent=None):
        super(NavigationBarPushButton, self).__init__(icon, text, isSelectable, parent)
        self.iconAni = IconSlideAnimation(self)  # 图标滑动动画
        self._selectedIcon = selectedIcon
        self._isSelectedTextVisible = True

        self.setFixedSize(64, 58)  # 设置按钮大小
        setFont(self, 11)  # 设置字体大小

    # 绘制事件
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)

        # 绘制选中按钮样式
        if self.isSelected:
            painter.setBrush(QColor(214, 75, 84))  # 设置选中背景颜色
            painter.drawRoundedRect(self.rect().adjusted(4, 0, -4, 0), 10, 10)

        elif self.isPressed or self.isEnter:
            c = 255 if isDarkTheme() else 0
            alpha = 9 if self.isEnter else 6
            painter.setBrush(QColor(c, c, c, alpha))
            painter.drawRoundedRect(self.rect().adjusted(4, 0, -4, 0), 10, 10)

        # 绘制图标
        if (self.isPressed or not self.isEnter) and not self.isSelected:
            painter.setOpacity(0.6)
        if not self.isEnabled():
            painter.setOpacity(0.4)

        if self._isSelectedTextVisible:
            rect = QRectF(22, 13, 20, 20)
        else:
            rect = QRectF(22, 13 + self.iconAni.offset, 20, 20)

        selectedIcon = self._selectedIcon or self._icon

        if isinstance(selectedIcon, FluentIconBase) and self.isSelected:
            if isDarkTheme():
                selectedIcon.render(painter, rect, fill="#ffffff")
            else:
                selectedIcon.render(painter, rect, fill="#ffffff")
        elif self.isSelected:
            drawIcon(selectedIcon, painter, rect)
        else:
            drawIcon(self._icon, painter, rect)

        if self.isSelected and not self._isSelectedTextVisible:
            return

        # 绘制文字
        painter.setPen(QColor(255, 255, 255) if self.isSelected else QColor(158, 158, 158))   

        painter.setFont(self.font())
        rect = QRect(0, 32, self.width(), 26)
        painter.drawText(rect, Qt.AlignCenter, self.text())
        
class OdTitleBar(SplitTitleBar):
    """ One Dragon 自定义标题栏 """

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
        layout.addSpacerItem(QSpacerItem(8, 20, QSizePolicy.Minimum, QSizePolicy.Minimum))

        # 添加窗口标题
        self.titleLabel = QLabel(self)
        layout.addWidget(self.titleLabel, 0, Qt.AlignLeft | Qt.AlignTop)
        self.titleLabel.setObjectName('titleLabel')

        self.window().windowTitleChanged.connect(self.setTitle)

        # 扩展空白项
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # 将新创建的布局插入到标题栏的主布局中
        self.hBoxLayout.insertLayout(0, layout)

    def setIcon(self, icon: QIcon):
        self.iconLabel.setPixmap(icon.pixmap(18, 18))

    def setTitle(self, title: str):
        self.titleLabel.setText(title)
