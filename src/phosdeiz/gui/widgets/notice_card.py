import requests
import webbrowser

from PySide6.QtCore import Qt, QSize, QTimer, QThread, Signal
from PySide6.QtGui import QPixmap, QFont, QPainterPath, QRegion, QColor
from PySide6.QtWidgets import (
    QVBoxLayout,
    QListWidgetItem,
    QWidget,
    QLabel,
    QHBoxLayout,
    QStackedWidget,
)

from qfluentwidgets import SimpleCardWidget, HorizontalFlipView, ListWidget

from .label import EllipsisLabel
from .pivot import CustomListItemDelegate, PhosPivot


class DataFetcher(QThread):
    data_fetched = Signal(dict)

    BASE_URL = "https://hyp-api.mihoyo.com/hyp/hyp-connect/api/getGameContent"
    LAUNCHER_ID = "jGHBHlcOq1"
    GAME_ID = "x6znKlJ0xK"

    def run(self):
        try:
            response = requests.get(
                f"{DataFetcher.BASE_URL}?launcher_id={DataFetcher.LAUNCHER_ID}&game_id={DataFetcher.GAME_ID}&language=zh-cn",
                verify=False,
                timeout=10,
            )
            response.raise_for_status()
            self.data_fetched.emit(response.json())
        except requests.RequestException as e:
            self.data_fetched.emit({"error": str(e)})


class NoticeCard(SimpleCardWidget):
    def __init__(self):
        super().__init__()
        self.setBorderRadius(10)
        self.setFixedWidth(351)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(3, 3, 0, 0)
        self.mainLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.error_label = QLabel("无法获取数据")
        self.error_label.setWordWrap(True)
        self.error_label.setObjectName("error")
        self.error_label.hide()
        self.mainLayout.addWidget(self.error_label)

        self.banners, self.banner_urls, self.posts = (
            [],
            [],
            {"announces": [], "activities": [], "infos": []},
        )
        self.setup_ui()
        self.fetch_data()

    def _normalBackgroundColor(self):
        return QColor(255, 255, 255, 13)

    def fetch_data(self):
        self.fetcher = DataFetcher()
        self.fetcher.data_fetched.connect(self.handle_data)
        self.fetcher.start()

    def handle_data(self, content):
        if "error" in content:
            self.error_label.setText(f"无法获取数据: {content['error']}")
            self.error_label.setFixedSize(330, 160)
            self.error_label.show()
            self.flipView.hide()
            self.update_ui()
            return
        self.load_banners(content["data"]["content"]["banners"])
        self.load_posts(content["data"]["content"]["posts"])
        self.error_label.hide()
        self.update_ui()

    def load_banners(self, banners):
        pixel_ratio = self.devicePixelRatio()  # 获取设备像素比
        for banner in banners:
            try:
                response = requests.get(banner["image"]["url"])
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)

                # 缩放图片，确保清晰
                size = QSize(pixmap.width(), pixmap.height())
                pixmap = pixmap.scaled(
                    size * pixel_ratio,  # 按设备像素比缩放
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation,
                )
                pixmap.setDevicePixelRatio(pixel_ratio)  # 设置设备像素比
                self.banners.append(pixmap)
                self.banner_urls.append(banner["image"]["link"])
            except Exception as e:
                print(f"加载图片失败: {e}")

    def load_posts(self, posts):
        post_types = {
            "POST_TYPE_ANNOUNCE": "announces",
            "POST_TYPE_ACTIVITY": "activities",
            "POST_TYPE_INFO": "infos",
        }
        for post in posts:
            if (entry := post_types.get(post["type"])) is not None:
                self.posts[entry].append(
                    {"title": post["title"], "url": post["link"], "date": post["date"]}
                )

    def setup_ui(self):
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
        QTimer.singleShot(7000, self.scrollNext)

        self.pivot = PhosPivot()
        self.stackedWidget = QStackedWidget(self)
        self.stackedWidget.setContentsMargins(0, 0, 5, 0)
        self.stackedWidget.setFixedHeight(60)
        self.activityWidget, self.announceWidget, self.infoWidget = (
            ListWidget(),
            ListWidget(),
            ListWidget(),
        )

        types = ["activities", "announces", "infos"]
        type_names = ["活动", "公告", "资讯"]
        for i, w in enumerate(
            [self.activityWidget, self.announceWidget, self.infoWidget]
        ):
            type = types[i]
            name = type_names[i]
            self.add_posts_to_widget(w, type)
            w.setItemDelegate(CustomListItemDelegate(w))
            w.itemClicked.connect(
                lambda _, widget=w, type=type: self.open_post_link(widget, type)
            )
            self.addSubInterface(w, type, name)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.activityWidget)
        self.pivot.setCurrentItem(self.activityWidget.objectName())
        self.mainLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.mainLayout.addWidget(self.stackedWidget)

    def update_ui(self):
        self.flipView.addImages(self.banners)
        for widget, type in zip(
            [self.activityWidget, self.announceWidget, self.infoWidget],
            ["activities", "announces", "infos"],
        ):
            self.add_posts_to_widget(widget, type)

    def scrollNext(self):
        if self.banners:
            self.flipView.setCurrentIndex(
                (self.flipView.currentIndex() + 1) % len(self.banners)
            )

    def addSubInterface(self, widget: ListWidget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())

    def open_banner_link(self):
        if self.banner_urls:
            webbrowser.open(self.banner_urls[self.flipView.currentIndex()])

    def open_post_link(self, widget: ListWidget, type: str):
        if self.posts[type]:
            webbrowser.open(self.posts[type][widget.currentIndex().row()]["url"])

    def add_posts_to_widget(self, widget: ListWidget, type: str):
        for post in self.posts[type][:2]:
            item_widget = self.create_post_widget(post)
            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            widget.addItem(item)
            widget.setItemWidget(item, item_widget)

    def create_post_widget(self, post):
        item_widget = QWidget()
        layout = QHBoxLayout(item_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        title_label = EllipsisLabel(post["title"])
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignLeft)
        title_label.setFixedWidth(280)
        title_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(title_label)

        date_label = QLabel(post["date"])
        date_label.setObjectName("date")
        date_label.setAlignment(Qt.AlignRight)
        date_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(date_label)

        layout.setStretch(0, 1)
        layout.setStretch(1, 0)
        return item_widget
