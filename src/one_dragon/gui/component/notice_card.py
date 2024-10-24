import requests
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QPixmap, QFont, QPainterPath, QRegion
from PySide6.QtWidgets import (
    QVBoxLayout,
    QListWidgetItem,
    QWidget,
    QLabel,
    QHBoxLayout,
    QStackedWidget,
)
from qfluentwidgets import (
    SimpleCardWidget,
    HorizontalFlipView,
    ListWidget,
)
import webbrowser

from one_dragon.gui.component.ellipsis_label import EllipsisLabel
from one_dragon.gui.component.oni_pivot import CustomListItemDelegate, OniPivot


class NoticeCard(SimpleCardWidget):
    def __init__(self):
        super().__init__()

        self.setBorderRadius(10)
        self.setFixedWidth(351)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(3, 3, 3, 0)
        self.mainLayout.setAlignment(Qt.AlignLeft)

        response = requests.get(
            "https://hyp-api.mihoyo.com/hyp/hyp-connect/api/getGameContent?launcher_id=jGHBHlcOq1&game_id=x6znKlJ0xK&language=zh-cn"
        ).json()
        content = response["data"]["content"]

        self.banners = []
        self.banner_urls = []

        for banner in content["banners"]:
            pixmap = QPixmap()
            pixmap.loadFromData(requests.get(banner["image"]["url"]).content)
            self.banners.append(pixmap)
            self.banner_urls.append(banner["image"]["link"])

        # 创建 flipView
        self.flipView = HorizontalFlipView(self)
        self.flipView.addImages(self.banners)
        self.flipView.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.flipView.setItemSize(QSize(345, 160))
        self.flipView.setFixedSize(QSize(345, 160))
        self.flipView.itemClicked.connect(self.open_banner_link)

        # 实现遮罩
        path = QPainterPath()
        path.addRoundedRect(self.flipView.rect(), 10, 10, Qt.SizeMode.AbsoluteSize)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.flipView.setMask(region)

        self.mainLayout.addWidget(self.flipView)

        # 设置自动滚动
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.scrollNext)
        self.timer.start(7000)

        # 创建导航栏
        self.pivot = OniPivot()
        self.pivot.setFont(QFont("Microsoft YaHei", 8, QFont.Weight.Bold))
        self.pivot.setContentsMargins(0, 0, 0, 0)
        self.pivot.setMaximumHeight(32)
        self.pivot.setObjectName("Pivot")

        # 处理信号
        self.posts = {"announces": [], "activities": [], "infos": []}

        post_types = {
            "POST_TYPE_ANNOUNCE": "announces",
            "POST_TYPE_ACTIVITY": "activities",
            "POST_TYPE_INFO": "infos",
        }

        for post in content["posts"]:
            post_type = post["type"]
            if post_type in post_types:
                entry = {
                    "title": post["title"],
                    "url": post["link"],
                    "date": post["date"],
                }
                self.posts[post_types[post_type]].append(entry)

        # 窗体
        self.stackedWidget = QStackedWidget(self)

        # 各个页面
        self.activityWidget = ListWidget()
        self.announceWidget = ListWidget()
        self.infoWidget = ListWidget()

        self.add_posts_to_widget(self.activityWidget, "activities")
        self.add_posts_to_widget(self.announceWidget, "announces")
        self.add_posts_to_widget(self.infoWidget, "infos")

        self.activityWidget.setItemDelegate(CustomListItemDelegate(self.activityWidget))
        self.announceWidget.setItemDelegate(CustomListItemDelegate(self.announceWidget))
        self.infoWidget.setItemDelegate(CustomListItemDelegate(self.infoWidget))

        self.activityWidget.itemClicked.connect(
            lambda: self.open_post_link(self.activityWidget, "activities")
        )
        self.announceWidget.itemClicked.connect(
            lambda: self.open_post_link(self.announceWidget, "announces")
        )
        self.infoWidget.itemClicked.connect(
            lambda: self.open_post_link(self.infoWidget, "infos")
        )

        # 添加标签页
        self.addSubInterface(self.activityWidget, "activityWidget", "活动")
        self.addSubInterface(self.announceWidget, "announceWidget", "公告")
        self.addSubInterface(self.infoWidget, "infoWidget", "资讯")

        # 连接信号并初始化当前标签页
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.activityWidget)
        self.pivot.setCurrentItem(self.activityWidget.objectName())

        self.mainLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.mainLayout.addWidget(self.stackedWidget)

    def scrollNext(self):
        """scroll to next item"""
        if self.flipView.currentIndex() + 1 <= len(self.banners) - 1:
            self.flipView.setCurrentIndex(self.flipView.currentIndex() + 1)
        else:
            self.flipView.setCurrentIndex(0)

    def addSubInterface(self, widget: QLabel, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)

        # 使用全局唯一的 objectName 作为路由键
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())

    def open_banner_link(self):
        webbrowser.open(self.banner_urls[self.flipView.currentIndex()])

    def open_post_link(self, widget: ListWidget, type: str):
        webbrowser.open(self.posts[type][widget.currentIndex().row()]["url"])

    def add_posts_to_widget(self, widget: ListWidget, type: str):
        for post in self.posts[type][:2]:
            item_widget = QWidget()
            layout = QHBoxLayout(item_widget)
            layout.setContentsMargins(0, 0, 0, 0)

            title_label = EllipsisLabel(post["title"])
            title_label.setAlignment(Qt.AlignLeft)
            title_label.setObjectName("title")
            title_label.setFont(QFont("Microsoft YaHei", 10))
            title_label.setTextInteractionFlags(Qt.NoTextInteraction)
            title_label.setFixedWidth(280)
            layout.addWidget(title_label)

            date_label = QLabel(f"{post['date']} ")
            date_label.setAlignment(Qt.AlignRight)
            date_label.setObjectName("date")
            date_label.setFont(QFont("Microsoft YaHei", 10))
            date_label.setTextInteractionFlags(Qt.NoTextInteraction)
            layout.addWidget(date_label)

            layout.setStretch(0, 1)  # 标题占用可用空间
            layout.setStretch(1, 0)  # 日期不占用多余空间

            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            widget.addItem(item)
            widget.setItemWidget(item, item_widget)
