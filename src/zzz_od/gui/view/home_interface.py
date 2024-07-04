import os

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPainterPath, QLinearGradient
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSpacerItem, QSizePolicy
from qfluentwidgets import isDarkTheme, FluentIcon

from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.link_card import LinkCardView
from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt


class BannerWidget(QWidget):
    """ Banner widget """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(336)

        self.vBoxLayout = QVBoxLayout(self)
        self.banner = QPixmap(os.path.join(os_utils.get_path_under_work_dir('assets', 'ui'), '1.png'))
        self.linkCardView = LinkCardView(self)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 20, 0, 0)
        self.vBoxLayout.addWidget(self.linkCardView, 1, Qt.AlignmentFlag.AlignBottom)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.vBoxLayout.addItem(spacer)

        self.linkCardView.addCard(
            FluentIcon.GITHUB,
            gt('主页', 'ui'),
            self.tr(
                '喜欢本项目请前往主页点Star'),
            "https://github.com/DoctorReid/ZenlessZoneZero-OneDragon"
        )

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.SmoothPixmapTransform | QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        w, h = self.width(), self.height()
        path.addRoundedRect(QRectF(0, 0, w, h), 10, 10)
        path.addRect(QRectF(0, h-50, 50, 50))
        path.addRect(QRectF(w-50, 0, 50, 50))
        path.addRect(QRectF(w-50, h-50, 50, 50))
        path = path.simplified()

        # init linear gradient effect
        gradient = QLinearGradient(0, 0, 0, h)

        # draw background color
        if not isDarkTheme():
            gradient.setColorAt(0, QColor(207, 216, 228, 255))
            gradient.setColorAt(1, QColor(207, 216, 228, 0))
        else:
            gradient.setColorAt(0, QColor(0, 0, 0, 255))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))

        painter.fillPath(path, QBrush(gradient))

        # draw banner image
        pixmap = self.banner.scaled(
            self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        painter.fillPath(path, QBrush(pixmap))


class HomeInterface(VerticalScrollInterface):
    """ Home interface """

    def __init__(self, parent=None):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        content_layout.setContentsMargins(0, 0, 0, 36)
        content_layout.setSpacing(40)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        banner = BannerWidget()
        content_layout.addWidget(banner)

        VerticalScrollInterface.__init__(self, parent=parent,
                                         content_widget=content_widget, object_name='home_interface',
                                         nav_text_cn='主页', nav_icon=FluentIcon.HOME)
