
import sys

from PySide6.QtCore import Qt, QPropertyAnimation, Property, QRect, QRectF
from PySide6.QtGui import QIcon, QPainter, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSpacerItem, QSizePolicy
from qfluentwidgets import FluentStyleSheet, drawIcon, isDarkTheme, FluentIcon as FIF, setFont, SplitTitleBar, \
    NavigationBarPushButton, MSFluentWindow, SingleDirectionScrollArea, NavigationBar, qrouter, FluentIconBase, \
    NavigationItemPosition
from typing import Union


#继承MSFluentWindow并重绘部分函数
class OneDragonWindow(MSFluentWindow):

    def __init__(self, parent=None):

        self._isAeroEnabled = False

        super(MSFluentWindow, self).__init__(parent=parent)  # 不初始化MSFluentWindow 初始化其父类

        self.setTitleBar(OdTitleBar(self))
        
        self.navigationInterface = OneDragonNavigationBar(self)

        # 继承MSFluentWindow的部分属性
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackedWidget, 1)

        self.titleBar.raise_()
        self.titleBar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

    # 补充磨砂效果
    def setAeroEffectEnabled(self, isEnabled: bool):

        if sys.platform != 'win32':
            return

        self._isAeroEnabled = isEnabled

        if isEnabled:
            self.windowEffect.setAeroEffect(int(self.winId()))
        else:
            self.windowEffect.removeBackgroundEffect(self.winId())

        self.setBackgroundColor(self._normalBackgroundColor())

    def isAeroEffectEnabled(self):
        return self._isAeroEnabled
        
    def _normalBackgroundColor(self):
        if not self.isAeroEffectEnabled():
            return self._darkBackgroundColor if isDarkTheme() else self._lightBackgroundColor

        return QColor(0, 0, 0, 0)

    def _onThemeChangedFinished(self):
        if self.isAeroEffectEnabled():
            self.windowEffect.setAeroEffect(self.winId(), isDarkTheme())

class OneDragonNavigationBar(NavigationBar):

    def __init__(self, parent=None):
        super(NavigationBar, self).__init__(parent)

        self.scrollArea = SingleDirectionScrollArea(self)
        self.scrollWidget = QWidget()


        self.vBoxLayout = QVBoxLayout(self)
        self.topLayout = QVBoxLayout()
        self.bottomLayout = QVBoxLayout()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)

        self.items = {}
        self.history = qrouter

        self.__initWidget()

    def __initWidget(self):
        self.resize(48, self.height())
        self.setAttribute(Qt.WA_StyledBackground)
        self.window().installEventFilter(self)

        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)

        self.scrollWidget.setObjectName('scrollWidget')
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self)
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self.scrollWidget)
        self.__initLayout()

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(0, 5, 0, 5)
        self.topLayout.setContentsMargins(4, 0, 4, 0)
        self.bottomLayout.setContentsMargins(4, 0, 4, 0)
        self.scrollLayout.setContentsMargins(4, 0, 4, 0)
        self.vBoxLayout.setSpacing(4)
        self.topLayout.setSpacing(4)
        self.bottomLayout.setSpacing(4)
        self.scrollLayout.setSpacing(4)

        self.vBoxLayout.addLayout(self.topLayout, 0)
        self.vBoxLayout.addWidget(self.scrollArea)
        self.vBoxLayout.addLayout(self.bottomLayout, 0)

        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.topLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.bottomLayout.setAlignment(Qt.AlignBottom)

    def insertItem(self, index: int, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str, onClick=None,
                   selectable=True, selectedIcon=None, position=NavigationItemPosition.TOP):
        if routeKey in self.items:
            return

        w = OdNavigationBarPushButton(icon, text, selectable, selectedIcon, self)
        self.insertWidget(index, routeKey, w, onClick, position)
        return w

class IconSlideAnimation(QPropertyAnimation):
    """ Icon sliding animation """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0
        self.maxOffset = 6
        self.setTargetObject(self)
        self.setPropertyName(b"offset")

    def getOffset(self):
        return self._offset

    def setOffset(self, value: float):
        self._offset = value
        self.parent().update()

    def slideDown(self):
        """ slide down """
        self.setEndValue(self.maxOffset)
        self.setDuration(100)
        self.start()

    def slideUp(self):
        """ slide up """
        self.setEndValue(0)
        self.setDuration(100)
        self.start()

    offset = Property(float, getOffset, setOffset)

class OdNavigationBarPushButton(NavigationBarPushButton):
    """ Navigation bar push button """

    def __init__(self, icon: Union[str, QIcon, FIF], text: str, isSelectable: bool, selectedIcon=None, parent=None):
        super(NavigationBarPushButton, self).__init__(icon, text, isSelectable, parent)
        self.iconAni = IconSlideAnimation(self)
        self._selectedIcon = selectedIcon
        self._isSelectedTextVisible = True

        self.setFixedSize(64, 58)
        setFont(self, 11)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)

        # 绘制选中按钮样式
        if self.isSelected:
            painter.setBrush(QColor(214,75,84))
            painter.drawRoundedRect(self.rect().adjusted(4, 0, -4, 0), 10, 10)

        elif self.isPressed or self.isEnter:
            c = 255 if isDarkTheme() else 0
            alpha = 9 if self.isEnter else 6
            painter.setBrush(QColor(c, c, c, alpha))
            painter.drawRoundedRect(self.rect().adjusted(4, 0, -4, 0), 10, 10)

        # draw icon
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

        # draw text
        if self.isSelected:
            painter.setPen(Qt.white)
        else:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)

        painter.setFont(self.font())
        rect = QRect(0, 32, self.width(), 26)
        painter.drawText(rect, Qt.AlignCenter, self.text())

class OdTitleBar(SplitTitleBar):
    """ One Dragon Title Bar """

    def __init__(self, parent=None):
        super(SplitTitleBar, self).__init__(parent)
        self.setFixedHeight(32)

        # Create a new layout to hold icon and title together
        layout = QHBoxLayout()
        layout.setContentsMargins(84, 10, 0, 0)  # Left 64px, Top 12px

        # Add window icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(18, 18)
        layout.addWidget(self.iconLabel, 0, Qt.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.window().windowIconChanged.connect(self.setIcon)

        layout.addSpacerItem(QSpacerItem(8, 20, QSizePolicy.Minimum, QSizePolicy.Minimum))

        # Add title label
        self.titleLabel = QLabel(self)
        layout.addWidget(self.titleLabel, 0, Qt.AlignLeft | Qt.AlignTop)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

        # Add a spacer at the end to push the title to the left
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Integrate iconAndTitleLayout into the main hBoxLayout
        self.hBoxLayout.insertLayout(0, layout)