import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QImage
from PySide6.QtWidgets import QWidget
from one_dragon.utils.log_utils import log
import datetime

class Banner(QWidget):
    """展示带有圆角的固定大小横幅小部件"""

    def __init__(self, image_path: str, parent=None):
        QWidget.__init__(self, parent)
        self.image_path = image_path
        self.banner_image = self.load_banner_image(image_path)
        self.scaled_image = None
        self.update_scaled_image()

    def load_banner_image(self, image_path: str) -> QImage:
        """加载横幅图片，或创建渐变备用图片"""
        if os.path.isfile(image_path):
            return QImage(image_path)
        return self._create_fallback_image()

    def _create_fallback_image(self) -> QImage:
        """创建渐变备用图片"""
        fallback_image = QImage(2560, 1280, QImage.Format.Format_RGB32)  # 使用原始图片的大小
        fallback_image.fill(Qt.GlobalColor.gray)
        return fallback_image

    def update_scaled_image(self) -> None:
        """
        更新缩放后的图片
        :return:
        """
        if self.banner_image.isNull():
            return
        log.info(f"[Banner] update_scaled_image called, widget size: {self.size()}")
        scaled_image = self.banner_image.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        self.scaled_image = QPixmap.fromImage(scaled_image)
        self.update()

    def paintEvent(self, event):
        """重载 paintEvent 以绘制缩放后的图片"""
        if self.scaled_image:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            # 创建圆角路径
            path = QPainterPath()
            path.addRoundedRect(self.rect(), 20, 20)
            painter.setClipPath(path)

            # 计算绘制位置，使图片居中
            x = (self.width() - self.scaled_image.width()) // 2
            y = (self.height() - self.scaled_image.height()) // 2

            # 绘制缩放后的图片
            painter.drawPixmap(x, y, self.scaled_image)

    def resizeEvent(self, event):
        """重载 resizeEvent 以更新缩放后的图片"""
        self.update_scaled_image()
        QWidget.resizeEvent(self, event)

    def set_percentage_size(self, width_percentage, height_percentage):
        """设置 Banner 的大小为窗口大小的百分比"""
        parent = self.parentWidget()
        if parent:
            new_width = int(parent.width() * width_percentage)
            new_height = int(parent.height() * height_percentage)
            self.setFixedSize(new_width, new_height)
            self.update_scaled_image()

    def set_banner_image(self, image_path: str) -> None:
        """
        设置背景图片
        :param image_path: 图片路径
        :return:
        """
        log.info(f"[Banner] set_banner_image called at {datetime.datetime.now()} with path: {image_path}")
        self.banner_image = QImage(image_path)
        log.info(f"[Banner] banner_image isNull: {self.banner_image.isNull()}")
        self.update_scaled_image()
