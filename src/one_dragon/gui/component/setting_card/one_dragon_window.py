
from typing import Dict, Union
import sys

from PySide6.QtCore import Qt,QPropertyAnimation,Property,QRect,QRectF
from PySide6.QtGui import QIcon, QPainter, QColor
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication

from qfluentwidgets import FluentStyleSheet,drawIcon,isDarkTheme,themeColor,FluentIcon as FIF,setFont,NavigationBarPushButton,MSFluentWindow,MSFluentTitleBar,SingleDirectionScrollArea,NavigationBar,NavigationWidget,qrouter,FluentIconBase,NavigationItemPosition



class OneDragonWindow(MSFluentWindow):
    """ Fluent window in Microsoft Store style """

    def __init__(self, parent=None):
        super(MSFluentWindow, self).__init__(parent)
        self.setTitleBar(MSFluentTitleBar(self))

        self.navigationInterface = OneDragonNavigationBar(self)
        # self.navigationInterface.setStyleSheet("background-color: #1a1a21;")
        # self.stackedWidget.setStyleSheet("background-color: #13131a;")
        # self.titleBar.setStyleSheet("background-color: #1a1a21;")
        # initialize layout
        self.hBoxLayout.setContentsMargins(0, 48, 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackedWidget, 1)

        self.titleBar.raise_()
        self.titleBar.setAttribute(Qt.WA_StyledBackground)




class OneDragonNavigationBar(NavigationBar):

    def __init__(self, parent=None):
        super(NavigationBar, self).__init__(parent)

        self.scrollArea = SingleDirectionScrollArea(self)
        self.scrollWidget = QWidget()


        self.vBoxLayout = QVBoxLayout(self)
        self.topLayout = QVBoxLayout()
        self.bottomLayout = QVBoxLayout()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)

        self.items = {}   # type: Dict[str, NavigationWidget]
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
        """ insert navigation tree item

        Parameters
        ----------
        index: int
            the insert position of parent widget

        routeKey: str
            the unique name of item

        icon: str | QIcon | FluentIconBase
            the icon of navigation item

        text: str
            the text of navigation item

        onClick: callable
            the slot connected to item clicked signal

        selectable: bool
            whether the item is selectable

        selectedIcon: str | QIcon | FluentIconBase
            the icon of navigation item in selected state

        position: NavigationItemPosition
            where the button is added
        """
        if routeKey in self.items:
            return

        w = OneDragonNavigationBarPushButton(icon, text, selectable, selectedIcon, self)
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

class OneDragonNavigationBarPushButton(NavigationBarPushButton):
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

        # draw background
        if self.isSelected:
            # painter.setBrush(QColor('#d64b54') if isDarkTheme() else Qt.white)
            painter.setBrush(QColor('#d64b54'))
            painter.drawRoundedRect(self.rect(), 5, 5)

            # draw indicator
            # painter.setBrush(Qt.white)
            # if not self.isPressed:
            #     painter.drawRoundedRect(0, 16, 4, 24, 2, 2)
            # else:
            #     painter.drawRoundedRect(0, 19, 4, 18, 2, 2)
        elif self.isPressed or self.isEnter:
            c = 255 if isDarkTheme() else 0
            alpha = 9 if self.isEnter else 6
            painter.setBrush(QColor(c, c, c, alpha))
            painter.drawRoundedRect(self.rect(), 5, 5)

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